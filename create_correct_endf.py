"""Create correctly formatted ENDF files."""
from pathlib import Path

def format_endf_line(data_str, mat=125, mf=0, mt=0, line_num=0):
    """Format an ENDF line correctly.
    
    ENDF-6 format (0-indexed Python):
    - Cols 0-65: Data (66 characters)
    - Cols 66-69: MAT (4 characters, right-aligned)
    - Col 70-71: MF (2 characters, right-aligned)
    - Cols 72-74: MT (3 characters, right-aligned)
    - Cols 75-79: Line number (5 characters, right-aligned)
    Total: 80 characters
    """
    # Ensure data is exactly 66 chars
    data_padded = data_str.ljust(66)[:66]
    
    # Format control fields (right-aligned)
    mat_str = f"{mat:4d}"[:4].rjust(4)
    mf_str = f"{mf:2d}"[:2].rjust(2)
    mt_str = f"{mt:3d}"[:3].rjust(3)
    line_str = f"{line_num:5d}"[:5].rjust(5)
    
    line = data_padded + mat_str + mf_str + mt_str + line_str
    assert len(line) == 80, f"Line length should be 80, got {len(line)}"
    return line

def format_value(val):
    """Format a number in ENDF 11-character format."""
    if val == 0.0:
        return " 0.000000+0"
    # Format as: sign, 1 digit, decimal, 6 digits, E, sign, 2 digit exponent
    s = f"{val:.6E}".upper()
    # ENDF format uses format like " 1.234567+8" (11 chars total)
    # Parse the scientific notation
    if 'E' in s:
        mantissa, exp = s.split('E')
        exp_int = int(exp)
        mantissa_float = float(mantissa)
        # Ensure single digit before decimal
        if abs(mantissa_float) >= 10:
            mantissa_float /= 10
            exp_int += 1
        elif abs(mantissa_float) < 1 and mantissa_float != 0:
            mantissa_float *= 10
            exp_int -= 1
        # Format: sign + 1 digit + decimal + 6 digits + E + sign + 2 digit exp
        sign = '-' if mantissa_float < 0 else ' '
        mantissa_str = f"{abs(mantissa_float):.6f}".ljust(7)[:7]
        exp_sign = '+' if exp_int >= 0 else '-'
        return f"{sign}{mantissa_str}E{exp_sign}{abs(exp_int):02d}"
    return s[:11].rjust(11)

def create_u235_endf():
    """Create a correctly formatted U235 ENDF file."""
    lines = []
    
    # Header section: MF=1, MT=451
    # Line 1: Control record
    lines.append(format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=1, mt=451, line_num=1))
    # Line 2: ZA value (92235 = 92*1000 + 235)
    lines.append(format_endf_line(" 9.223500+4 2.350000+2          0          0          0          0", mat=125, mf=1, mt=451, line_num=2))
    lines.append(format_endf_line("", mat=125, mf=1, mt=451, line_num=0))  # Blank continuation
    
    # MF=3, MT=1 (Total cross-section)
    # Control record
    lines.append(format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=3, mt=1, line_num=1))
    # Interpolation record
    lines.append(format_endf_line(" 0.000000+0 0.000000+0          0          0          0          3", mat=125, mf=3, mt=1, line_num=2))
    # Data: (E, XS) pairs
    data1 = format_value(1.0) + format_value(100.0) + format_value(1e4) + format_value(120.0) + format_value(1e6) + format_value(150.0)
    lines.append(format_endf_line(data1, mat=125, mf=3, mt=1, line_num=3))
    data2 = format_value(2e6) + format_value(180.0) + format_value(5e6) + format_value(200.0) + format_value(1e7) + format_value(220.0)
    lines.append(format_endf_line(data2, mat=125, mf=3, mt=1, line_num=4))
    lines.append(format_endf_line("", mat=125, mf=0, mt=0, line_num=0))  # Blank
    
    # MF=3, MT=2 (Elastic)
    lines.append(format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=3, mt=2, line_num=1))
    lines.append(format_endf_line(" 0.000000+0 0.000000+0          0          0          0          3", mat=125, mf=3, mt=2, line_num=2))
    data3 = format_value(1.0) + format_value(80.0) + format_value(1e4) + format_value(90.0) + format_value(1e6) + format_value(110.0)
    lines.append(format_endf_line(data3, mat=125, mf=3, mt=2, line_num=3))
    data4 = format_value(2e6) + format_value(130.0) + format_value(5e6) + format_value(150.0) + format_value(1e7) + format_value(170.0)
    lines.append(format_endf_line(data4, mat=125, mf=3, mt=2, line_num=4))
    lines.append(format_endf_line("", mat=125, mf=0, mt=0, line_num=0))
    
    # MF=3, MT=18 (Fission)
    lines.append(format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=3, mt=18, line_num=1))
    lines.append(format_endf_line(" 0.000000+0 0.000000+0          0          0          0          3", mat=125, mf=3, mt=18, line_num=2))
    data5 = format_value(1e4) + format_value(15.0) + format_value(1e6) + format_value(50.0) + format_value(2e6) + format_value(70.0)
    lines.append(format_endf_line(data5, mat=125, mf=3, mt=18, line_num=3))
    data6 = format_value(5e6) + format_value(100.0) + format_value(1e7) + format_value(120.0)
    lines.append(format_endf_line(data6, mat=125, mf=3, mt=18, line_num=4))
    lines.append(format_endf_line("", mat=125, mf=0, mt=0, line_num=0))
    
    # MF=3, MT=102 (Capture)
    lines.append(format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=3, mt=102, line_num=1))
    lines.append(format_endf_line(" 0.000000+0 0.000000+0          0          0          0          3", mat=125, mf=3, mt=102, line_num=2))
    data7 = format_value(1.0) + format_value(5.0) + format_value(1e4) + format_value(10.0) + format_value(1e6) + format_value(20.0)
    lines.append(format_endf_line(data7, mat=125, mf=3, mt=102, line_num=3))
    data8 = format_value(2e6) + format_value(25.0) + format_value(5e6) + format_value(30.0) + format_value(1e7) + format_value(35.0)
    lines.append(format_endf_line(data8, mat=125, mf=3, mt=102, line_num=4))
    lines.append(format_endf_line("", mat=125, mf=0, mt=0, line_num=0))
    lines.append(format_endf_line("", mat=125, mf=0, mt=0, line_num=0))  # Final blank
    
    return "\n".join(lines)

# Test the format function
print("Testing format function:")
test_line = format_endf_line(" 1.001000+3 9.991673-1          0          0          0          0", mat=125, mf=1, mt=451, line_num=1)
print(f"Test line: [{test_line}]")
print(f"Length: {len(test_line)}")
print(f"MF at 70-72: [{test_line[70:72]}]")
print(f"MT at 72-75: [{test_line[72:75]}]")

# Create file
data_dir = Path("tests/data")
data_dir.mkdir(exist_ok=True)
content = create_u235_endf()
(data_dir / "sample_U235.endf").write_text(content)
print(f"\nCreated {data_dir / 'sample_U235.endf'}")

