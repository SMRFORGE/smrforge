"""Debug script to test ENDF file parsing."""
from pathlib import Path

# Test line format
test_line = " 1.001000+3 9.991673-1          0          0          0          0  125 1451  451"
print("Testing line format:")
print(f"Line: [{test_line}]")
print(f"Length: {len(test_line)}")
print(f"\nColumn breakdown:")
print(f"  0-65 (data): [{test_line[0:66]}]")
print(f"  66-69 (MAT): [{test_line[66:70]}]")
print(f"  70-72 (MF): [{test_line[70:72]}] = '{test_line[70:72]}'")
print(f"  72-75 (MT): [{test_line[72:75]}] = '{test_line[72:75]}'")
print(f"  75-80 (line): [{test_line[75:80]}]")

# The issue: line shows "1451  451" at end, but:
# - MF should be at 70-72
# - MT should be at 72-75
# So we need: "  1" at 70-72 and "451" at 72-75

# Correct format should be:
# Cols 0-65: data (66 chars)
# Cols 66-69: MAT = " 125" (4 chars, right-aligned)
# Col 70-72: MF = "  1" (2 chars, right-aligned)  
# Col 72-75: MT = "451" (3 chars, right-aligned)
# Col 75-80: line number = "    1" (5 chars)

# So the line should end with: " 125  1451    1"
# But we have: " 125 1451  451"

# Wait, let me check the ENDF format again. Maybe it's:
# Cols 66-69: MAT (4 chars)
# Col 70-72: MF (3 chars? or 2 chars?)
# Col 72-75: MT (3 chars)
# Col 75-80: line number (5 chars)

# Actually, looking at the minimal mock, it seems like:
# "125 1451  451" suggests MAT=125, then maybe MF=1 and MT=451 are together?
# Or maybe: MAT=125 (4 chars), then "1" (1 char?), then "451" (3 chars)?

# Let me check what the actual ENDF format is. According to ENDF-6 manual:
# Position 66-70: MAT (material number, 5 positions)
# Position 71-72: MF (file number, 2 positions) 
# Position 73-75: MT (section number, 3 positions)
# Position 76-80: line number (5 positions)

# So the format is: [66:71] = MAT (5 chars), [71:73] = MF (2 chars), [73:76] = MT (3 chars), [76:81] = line (5 chars)

print("\n\nAccording to ENDF-6 format:")
print("  Cols 66-70: MAT (5 positions)")
print("  Cols 71-72: MF (2 positions)")
print("  Cols 73-75: MT (3 positions)")
print("  Cols 76-80: Line (5 positions)")

print(f"\nRe-interpreting test line:")
print(f"  MAT [66:71]: [{test_line[66:71]}]")
print(f"  MF [71:73]: [{test_line[71:73]}]")
print(f"  MT [73:76]: [{test_line[73:76]}]")
print(f"  Line [76:81]: [{test_line[76:81] if len(test_line) > 80 else 'N/A'}]")

# But the parser code uses:
# line[70:72] for MF
# line[72:75] for MT
# This suggests 0-indexed: col 70-71 (2 chars) for MF, 72-74 (3 chars) for MT

print("\n\nParser uses (0-indexed):")
print(f"  MF [70:72]: [{test_line[70:72]}]")
print(f"  MT [72:75]: [{test_line[72:75]}]")
print("  This reads '45' for MF and '1  ' for MT, which is wrong!")

# The correct format should be:
# Line ends with: "125  1 451    1"
# Where: MAT=125 (4 chars, cols 66-69), space, MF=1 (2 chars, cols 70-71), space, MT=451 (3 chars, cols 72-74), Line=1 (5 chars, cols 75-79)

# Actually wait - if MAT is 5 positions (66-70), then:
# Position 71-72: MF (but parser uses 70-72, so maybe it's 70-71?)
# Let me check what makes sense...

print("\n\nTrying to construct correct format:")
# For MF=1, MT=451, MAT=125, line=1:
# Data (66 chars) + " 125" (MAT, 4 chars) + "  1" (MF, 3 chars?) + "451" (MT, 3 chars) + "    1" (line, 5 chars) = 81 chars
# That's too long!

# Maybe MAT is 4 chars (66-69), MF is 1 char at 70, MT is 3 chars (72-74), line is 5 chars (75-79)?
# Data (66) + MAT (4) + space (1) + MF (1) + space (1) + MT (3) + line (5) = 81 chars... still too long

# Let me look at the actual minimal mock line more carefully:
correct_format = " 1.001000+3 9.991673-1          0          0          0          0  125 1451  451"
print(f"Minimal mock line: [{correct_format}]")
print(f"Length: {len(correct_format)}")
print(f"Last 15 chars: [{correct_format[-15:]}]")
# This shows: "  125 1451  451"
# So: " 125" (MAT?), " 1" (MF?), "451" (MT?), and line number is missing or at end?

# Actually, I think the minimal mock in conftest.py might have the wrong format too!
# Let me check if there's a working example or if I need to figure out the correct format from scratch.
