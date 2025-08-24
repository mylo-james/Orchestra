"""Orchestra task execution engine (Story 1.3)."""

import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import threading
import signal
import subprocess
from contextlib import contextmanager

from orchestra.system.resource_loader import ResourceMetadata
from orchestra.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class TaskExecutionResult:
    """Result of task execution."""
    
    success: bool
    task_id: str
    execution_time: float = 0.0
    outputs: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    retry_count: int = 0
    steps_completed: int = 0
    total_steps: int = 0


class TaskExecutionError(Exception):
    """Exception raised during task execution."""
    
    def __init__(self, message: str, task_id: Optional[str] = None, step: Optional[str] = None):
        """Initialize task execution error."""
        super().__init__(message)
        self.task_id = task_id
        self.step = step


class TaskEngine:
    """Engine for executing Orchestra tasks."""
    
    def __init__(self, execution_timeout: int = 300, max_retries: int = 3):
        """
        Initialize the task engine.
        
        Args:
            execution_timeout: Maximum execution time in seconds
            max_retries: Maximum number of retry attempts
        """
        self.execution_timeout = execution_timeout
        self.max_retries = max_retries
        self._execution_lock = threading.RLock()
        self._active_executions: Dict[str, threading.Thread] = {}
        
        logger.info(f"Initialized TaskEngine (timeout: {execution_timeout}s, max_retries: {max_retries})")

    def execute_task(self, metadata: ResourceMetadata, content: str, context: Dict[str, Any]) -> TaskExecutionResult:
        """
        Execute a task with the given context.
        
        Args:
            metadata: Task metadata
            content: Task content (markdown)
            context: Execution context variables
            
        Returns:
            TaskExecutionResult with execution details
        """
        start_time = time.time()
        task_id = metadata.id
        
        logger.info(f"Starting task execution: {task_id}")
        
        # Initialize result
        result = TaskExecutionResult(
            success=False,
            task_id=task_id,
            outputs={}
        )
        
        # Parse task steps
        try:
            steps = self._parse_task_steps(content)
            result.total_steps = len(steps)
            
            if not steps:
                result.errors.append("No executable steps found in task")
                return result
            
            logger.debug(f"Parsed {len(steps)} steps for task: {task_id}")
            
        except Exception as e:
            result.errors.append(f"Failed to parse task steps: {str(e)}")
            return result
        
        # Execute with retries
        for attempt in range(self.max_retries + 1):
            try:
                result.retry_count = attempt
                
                # Execute task steps with timeout
                with self._timeout_context(self.execution_timeout):
                    execution_result = self._execute_task_steps(steps, context, metadata)
                    
                    result.success = True
                    result.outputs.update(execution_result.get("outputs", {}))
                    result.steps_completed = execution_result.get("steps_completed", 0)
                    
                    if execution_result.get("warnings"):
                        result.warnings.extend(execution_result["warnings"])
                    
                    break
                    
            except TimeoutError:
                error_msg = f"Task execution timeout after {self.execution_timeout}s"
                result.errors.append(error_msg)
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if attempt < self.max_retries:
                    time.sleep(1)  # Brief pause before retry
                    continue
                else:
                    break
                    
            except Exception as e:
                error_msg = f"Task execution failed: {str(e)}"
                result.errors.append(error_msg)
                logger.warning(f"{error_msg} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if attempt < self.max_retries:
                    time.sleep(1)  # Brief pause before retry
                    continue
                else:
                    break
        
        result.execution_time = time.time() - start_time
        
        if result.success:
            logger.info(f"Task execution completed: {task_id} (time: {result.execution_time:.3f}s, retries: {result.retry_count})")
        else:
            logger.error(f"Task execution failed: {task_id} (time: {result.execution_time:.3f}s, retries: {result.retry_count})")
        
        return result

    def _parse_task_steps(self, content: str) -> List[Dict[str, Any]]:
        """Parse task steps from markdown content."""
        steps = []
        
        # Look for sequential task execution sections
        sequential_match = re.search(r'##\s+SEQUENTIAL\s+Task\s+Execution.*?\n(.*?)(?=\n##|\n#|$)', content, re.DOTALL | re.IGNORECASE)
        if sequential_match:
            sequential_content = sequential_match.group(1)
            
            # Parse numbered steps
            step_matches = re.findall(r'###\s+(\d+)\.\s+(.+?)\n(.*?)(?=\n###|\n##|\n#|$)', sequential_content, re.DOTALL)
            
            for step_num, step_title, step_content in step_matches:
                step = {
                    "number": int(step_num),
                    "title": step_title.strip(),
                    "content": step_content.strip(),
                    "type": "sequential"
                }
                
                # Parse step instructions
                instructions = []
                for line in step_content.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        instructions.append(line[2:].strip())
                
                step["instructions"] = instructions
                steps.append(step)
        
        # Look for general task sections if no sequential steps found
        if not steps:
            # Parse general sections as steps
            section_matches = re.findall(r'##\s+(.+?)\n(.*?)(?=\n##|\n#|$)', content, re.DOTALL)
            
            for i, (section_title, section_content) in enumerate(section_matches):
                if section_title.lower() in ['purpose', 'description', 'notes']:
                    continue  # Skip metadata sections
                
                step = {
                    "number": i + 1,
                    "title": section_title.strip(),
                    "content": section_content.strip(),
                    "type": "general"
                }
                
                # Parse instructions
                instructions = []
                for line in section_content.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        instructions.append(line[2:].strip())
                
                step["instructions"] = instructions
                steps.append(step)
        
        # Sort steps by number
        steps.sort(key=lambda x: x["number"])
        
        return steps

    def _execute_task_steps(self, steps: List[Dict[str, Any]], context: Dict[str, Any], metadata: ResourceMetadata) -> Dict[str, Any]:
        """Execute task steps sequentially."""
        outputs = {}
        warnings = []
        steps_completed = 0
        
        logger.debug(f"Executing {len(steps)} steps for task: {metadata.id}")
        
        for step in steps:
            step_num = step["number"]
            step_title = step["title"]
            
            logger.debug(f"Executing step {step_num}: {step_title}")
            
            try:
                # Execute step instructions
                step_result = self._execute_step(step, context, metadata)
                
                # Merge step outputs
                if step_result.get("outputs"):
                    outputs.update(step_result["outputs"])
                
                if step_result.get("warnings"):
                    warnings.extend(step_result["warnings"])
                
                steps_completed += 1
                
                logger.debug(f"Completed step {step_num}: {step_title}")
                
            except Exception as e:
                error_msg = f"Step {step_num} failed: {str(e)}"
                logger.error(error_msg)
                raise TaskExecutionError(error_msg, metadata.id, step_title)
        
        return {
            "outputs": outputs,
            "warnings": warnings,
            "steps_completed": steps_completed
        }

    def _execute_step(self, step: Dict[str, Any], context: Dict[str, Any], metadata: ResourceMetadata) -> Dict[str, Any]:
        """Execute a single task step."""
        step_outputs = {}
        step_warnings = []
        
        instructions = step.get("instructions", [])
        
        for instruction in instructions:
            try:
                # Process instruction with context substitution
                processed_instruction = self._process_instruction(instruction, context)
                
                # Execute instruction based on type
                if processed_instruction.startswith("Load "):
                    # File loading instruction
                    result = self._execute_load_instruction(processed_instruction, context)
                    step_outputs.update(result)
                    
                elif processed_instruction.startswith("If "):
                    # Conditional instruction
                    result = self._execute_conditional_instruction(processed_instruction, context)
                    step_outputs.update(result)
                    
                elif "HALT" in processed_instruction:
                    # Halt instruction
                    raise TaskExecutionError(f"Task halted: {processed_instruction}")
                    
                else:
                    # General instruction - simulate execution
                    logger.debug(f"Processing instruction: {processed_instruction}")
                    step_outputs[f"instruction_{len(step_outputs)}"] = {
                        "instruction": processed_instruction,
                        "status": "processed",
                        "timestamp": time.time()
                    }
                    
            except Exception as e:
                step_warnings.append(f"Instruction failed: {instruction} - {str(e)}")
                logger.warning(f"Instruction failed: {instruction} - {str(e)}")
        
        return {
            "outputs": step_outputs,
            "warnings": step_warnings
        }

    def _process_instruction(self, instruction: str, context: Dict[str, Any]) -> str:
        """Process instruction with context variable substitution."""
        processed = instruction
        
        # Replace context variables in format {variable}
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in processed:
                processed = processed.replace(placeholder, str(value))
        
        return processed

    def _execute_load_instruction(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a load instruction."""
        # Extract file path from instruction
        file_match = re.search(r'Load\s+`([^`]+)`', instruction)
        if not file_match:
            file_match = re.search(r'Load\s+([^\s]+)', instruction)
        
        if file_match:
            file_path = file_match.group(1)
            
            # Simulate file loading
            return {
                "loaded_file": {
                    "path": file_path,
                    "status": "loaded",
                    "timestamp": time.time()
                }
            }
        
        return {}

    def _execute_conditional_instruction(self, instruction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a conditional instruction."""
        # Extract condition from instruction
        condition_match = re.search(r'If\s+(.+?),\s*(.+)', instruction)
        if condition_match:
            condition = condition_match.group(1)
            action = condition_match.group(2)
            
            # Simple condition evaluation (can be expanded)
            condition_result = self._evaluate_condition(condition, context)
            
            return {
                "condition": {
                    "expression": condition,
                    "result": condition_result,
                    "action": action,
                    "timestamp": time.time()
                }
            }
        
        return {}

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition."""
        # Simple condition evaluation - can be expanded
        if "not exist" in condition.lower():
            return False  # Simulate file not existing
        elif "exist" in condition.lower():
            return True   # Simulate file existing
        else:
            return True   # Default to true for other conditions

    @contextmanager
    def _timeout_context(self, timeout_seconds: int):
        """Context manager for execution timeout."""
        def timeout_handler(signum, frame):
            raise TimeoutError(f"Execution timeout after {timeout_seconds} seconds")
        
        # Set up timeout signal (Unix only)
        try:
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)
            yield
        except AttributeError:
            # Windows doesn't support SIGALRM, use threading timeout
            import threading
            
            timeout_event = threading.Event()
            
            def timeout_thread():
                timeout_event.wait(timeout_seconds)
                if not timeout_event.is_set():
                    raise TimeoutError(f"Execution timeout after {timeout_seconds} seconds")
            
            timer = threading.Thread(target=timeout_thread)
            timer.daemon = True
            timer.start()
            
            try:
                yield
                timeout_event.set()  # Cancel timeout
            finally:
                timeout_event.set()  # Ensure cleanup
        finally:
            try:
                signal.alarm(0)  # Cancel alarm
                signal.signal(signal.SIGALRM, old_handler)
            except (AttributeError, NameError):
                pass  # Windows or cleanup already done

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task.
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
        """
        with self._execution_lock:
            if task_id in self._active_executions:
                thread = self._active_executions[task_id]
                if thread.is_alive():
                    # Note: Python doesn't support thread termination
                    # This is a placeholder for cancellation logic
                    logger.warning(f"Task cancellation requested for {task_id} (not fully implemented)")
                    return True
                else:
                    del self._active_executions[task_id]
                    return False
            return False

    def get_active_tasks(self) -> List[str]:
        """Get list of currently active task IDs."""
        with self._execution_lock:
            return [task_id for task_id, thread in self._active_executions.items() if thread.is_alive()]

    def cleanup(self):
        """Clean up resources and stop active executions."""
        with self._execution_lock:
            active_tasks = self.get_active_tasks()
            if active_tasks:
                logger.info(f"Cleaning up {len(active_tasks)} active tasks")
                for task_id in active_tasks:
                    self.cancel_task(task_id)
            
            self._active_executions.clear()
        
        logger.info("TaskEngine cleanup completed")