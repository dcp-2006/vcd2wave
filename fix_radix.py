"""Fix radix onclick handlers in renderer.py."""

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Replace the problematic onclick with simpler version
# Old: onclick="cycleRadix(\'' + dn.replace(/'/g,'') + '\')"
# New: onclick="cycleRadix(\\'' + dn.replace(/'/g,'') + '\\')"
# Actually the current code should work. Let me check what's in the file.

# Find and examine the onclick lines
import re
matches = re.findall(r'onclick="cycleRadix.*?"', content)
for m in matches:
    print(f"Found: {m[:80]}")

# Check if there's a syntax issue - look for "\\'" in the content  
if "cycleRadix(\\\\'" in content:
    print("Issue: quadruple backslash found")
    content = content.replace("cycleRadix(\\\\'", "cycleRadix('")
    content = content.replace("+ '\\\\'", "+ '")
    
# Check for the pattern that causes issues
# The onclick should produce: onclick="cycleRadix('signalname')"
# In the JS source it should look like: onclick="cycleRadix(\' + name + \')"

with open('C:\\Users\\d1985\\Desktop\\vcd2wave\\vcd2wave\\renderer.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
