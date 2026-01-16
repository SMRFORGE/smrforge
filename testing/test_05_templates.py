#!/usr/bin/env python
"""
Template Library System Testing Script

This script tests the template-based reactor design library.

Usage:
    python test_05_templates.py
"""

import sys
import json
from pathlib import Path

try:
    import smrforge as smr
    from smrforge.workflows.templates import ReactorTemplate, TemplateLibrary
except ImportError:
    print("ERROR: SMRForge not installed. Run: pip install -e .")
    sys.exit(1)


def test_create_template_from_preset():
    """Test creating template from preset."""
    print("\n1. Testing create template from preset...")
    try:
        template = ReactorTemplate.from_preset('valar-10')
        print(f"✅ Created template: {type(template)}")
        print(f"   Template Name: {template.name}")
        print(f"   Parameters: {list(template.parameters.keys())}")
        
        # Save template
        template_file = Path('test_template.json')
        template.save(template_file)
        print(f"✅ Saved template to {template_file}")
        
        return template, template_file
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None


def test_load_template(template_file):
    """Test loading template from file."""
    print("\n2. Testing load template...")
    if template_file is None or not template_file.exists():
        print("⏭️  Skipped (no template file)")
        return None
    
    try:
        template = ReactorTemplate.load(template_file)
        print(f"✅ Loaded template: {template.name}")
        return template
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_instantiate_template(template):
    """Test instantiating template with defaults."""
    print("\n3. Testing instantiate template with defaults...")
    if template is None:
        print("⏭️  Skipped (no template)")
        return False
    
    try:
        reactor = template.instantiate()
        print(f"✅ Instantiated reactor: {type(reactor)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_instantiate_with_overrides(template):
    """Test instantiating template with parameter overrides."""
    print("\n4. Testing instantiate template with overrides...")
    if template is None:
        print("⏭️  Skipped (no template)")
        return False
    
    try:
        overrides = {'enrichment': 0.21, 'power': 300}
        reactor = template.instantiate(**overrides)
        print(f"✅ Instantiated with overrides: {type(reactor)}")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validate_template(template):
    """Test template validation."""
    print("\n5. Testing template validation...")
    if template is None:
        print("⏭️  Skipped (no template)")
        return False
    
    try:
        is_valid = template.validate()
        if is_valid:
            print("✅ Template validation passed")
            return True
        else:
            print("⚠️  Template validation found issues")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_template_library():
    """Test template library operations."""
    print("\n6. Testing template library...")
    try:
        library = TemplateLibrary()
        
        # Create a template
        template = ReactorTemplate.from_preset('valar-10')
        
        # Add to library
        library.save_template(template)
        print(f"✅ Added template to library")
        
        # Get from library
        retrieved = library.load_template(template.name)
        if retrieved is not None:
            print(f"✅ Retrieved template from library")
        
        # List templates
        templates = library.list_templates()
        print(f"✅ Library contains {len(templates)} templates")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Template Library System Testing")
    print("="*60)
    
    template, template_file = test_create_template_from_preset()
    loaded_template = test_load_template(template_file)
    
    # Use loaded template if available, otherwise use original
    test_template = loaded_template if loaded_template else template
    
    results = {}
    results['create_from_preset'] = template is not None
    results['load_template'] = loaded_template is not None
    results['instantiate_defaults'] = test_instantiate_template(test_template)
    results['instantiate_overrides'] = test_instantiate_with_overrides(test_template)
    results['validate_template'] = test_validate_template(test_template)
    results['template_library'] = test_template_library()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    if template_file and template_file.exists():
        template_file.unlink()
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
