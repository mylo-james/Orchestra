# Source Tree Integration

```
src/
  system/
    loader.py (enhanced overlays)
    resource_loader.py (new)
    task_engine.py (new)
    template_processor.py (new)
    checklist_engine.py (new)
projects/{project_id}/
  config.yaml
  personas/{po|architect|dev|qa}.overlay.yaml
  policies/*.yaml
  kb-seed/*.md
src/personas/base/{po|architect|dev|qa}.yaml
```
