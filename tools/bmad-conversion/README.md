# BMad Conversion Tools (Backup)

This directory contains the original BMad-to-Orchestra conversion tools used during the initial migration in Epic 1 (Stories 1.1-1.2).

## Status: BACKUP/LEGACY

These tools have served their purpose and are kept for:
- **Historical reference** - Understanding the conversion process
- **Future migrations** - If additional BMad content needs conversion
- **Rollback capability** - Emergency recovery if issues found with converted personas

## Files

- `bmad_inventory.py` - BMad content discovery and inventory system
- `bmad_persona_converter.py` - Core conversion logic from BMad to Orchestra YAML
- `test_bmad_*.py` - Comprehensive test suites for the conversion tools

## Usage

These tools are no longer part of the main Orchestra CLI. If needed for emergency use:

```bash
# Copy back to orchestra/system/ temporarily
cp tools/bmad-conversion/bmad_persona_converter.py orchestra/system/
# Re-add CLI commands if needed
```

## Migration Complete

✅ **11 Orchestra personas** successfully converted and active
✅ **All BMad references** cleaned up from main system
✅ **Rich persona content** with commands, tasks, templates, resources

The main Orchestra system now operates independently of BMad.