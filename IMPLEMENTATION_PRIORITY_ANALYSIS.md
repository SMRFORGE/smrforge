# Implementation Priority Analysis

## Comparison: Incomplete Methods vs. Not Implemented Stubs

### Option 1: Complete Incomplete Methods (Geometry Importers)

**Items:**
- OpenMC XML Import (`GeometryImporter.from_openmc_xml()`)
- Serpent Import (`GeometryImporter.from_serpent()`)

**Pros:**
1. ✅ **Completes existing functionality** - Finishes the geometry importers module
2. ✅ **Lower complexity** - Focused parsing tasks, not entire new modules
3. ✅ **Better ROI** - Completes existing API rather than creating new ones
4. ✅ **Interoperability value** - Allows importing from common reactor physics codes
5. ✅ **Clear scope** - Well-defined parsing tasks
6. ✅ **Incremental progress** - Can implement one format at a time
7. ✅ **Existing infrastructure** - Builds on existing `GeometryImporter` class

**Cons:**
1. ❌ Limited direct impact - JSON import already works
2. ❌ Requires understanding external formats (OpenMC CSG, Serpent syntax)
3. ❌ May need format specification documentation

**Complexity:** Medium (parsing-specific formats)
**Impact:** Medium (interoperability)
**Time Estimate:** 2-5 days per format

---

### Option 2: Implement Stub Modules (Not Implemented)

**Items:**
- Fuel Performance (`smrforge.fuel`)
- Optimization (`smrforge.optimization`)
- General I/O (`smrforge.io`)
- Control Systems (`smrforge.control`)
- Economics (`smrforge.economics`)

**Pros:**
1. ✅ **New capabilities** - Adds entirely new functionality
2. ✅ **User value** - Addresses complete missing feature areas
3. ✅ **Broader impact** - Each module serves distinct use cases

**Cons:**
1. ❌ **Much higher complexity** - Entire new modules from scratch
2. ❌ **Unclear requirements** - Need to define full APIs
3. ❌ **Longer development time** - Weeks/months per module
4. ❌ **Maintenance burden** - More code to maintain
5. ❌ **Optional features** - Many users may not need them
6. ❌ **Alternative solutions exist** - scipy.optimize, external fuel codes, etc.

**Complexity:** High (complete module design and implementation)
**Impact:** High (new capabilities) but varies by module
**Time Estimate:** 2-4 weeks per module (varies significantly)

---

## Recommendation: **Complete Incomplete Methods First**

### Rationale:

1. **Pragmatic Approach:**
   - Finish what you started (geometry importers)
   - Lower risk, faster wins
   - Incremental value delivery

2. **Better Development Practice:**
   - Complete existing APIs before adding new ones
   - Cleaner codebase (no incomplete methods)
   - Better user experience (fewer NotImplementedError surprises)

3. **Technical Benefits:**
   - Interoperability is valuable for reactor physics workflows
   - Users often need to convert between formats
   - These features are actually requested (importing from other codes)

4. **Resource Efficiency:**
   - 2-5 days vs. 2-4 weeks per module
   - Can complete both importers in ~1 week
   - Quick validation of value before committing to larger modules

5. **Stub Modules Are Truly Optional:**
   - Fuel Performance: External tools (BISON, FALCON) exist
   - Optimization: scipy.optimize covers most needs
   - Control Systems: Control rod geometry already exists
   - Economics: Domain-specific, likely low user demand
   - I/O: Pydantic serialization already provides this

---

## Suggested Implementation Order

### Phase 1: Complete Incomplete Methods (1-2 weeks)
1. **OpenMC XML Import** (3-5 days)
   - Parse OpenMC geometry.xml format
   - Convert CSG to SMRForge geometry
   - Test with sample OpenMC geometries

2. **Serpent Import** (2-4 days)
   - Parse Serpent input format
   - Extract geometry definitions
   - Convert to SMRForge geometry

### Phase 2: Evaluate Stub Modules (After Phase 1)
After completing importers, **reassess** which stub modules are actually needed:
- Gather user feedback
- Identify specific use cases
- Prioritize based on demand

### Phase 3: Stub Module Implementation (If Needed)
If stub modules are needed, suggested priority:
1. **Optimization** - Most general-purpose, high utility
2. **Fuel Performance** - If tight coupling with neutronics is needed
3. **Control Systems** - If going beyond control rod geometry
4. **Economics** - Lowest priority (specialized, external tools exist)
5. **General I/O** - Lowest priority (Pydantic already provides this)

---

## Conclusion

**Start with completing the incomplete methods (geometry importers).**

This approach:
- ✅ Completes existing functionality
- ✅ Provides quick wins
- ✅ Lowers risk
- ✅ Better code quality (no incomplete methods)
- ✅ Can reassess stub modules after seeing user needs

The stub modules are genuinely optional and can be implemented later if there's demonstrated demand. Completing the importers first gives you a fully functional geometry import system.

