import re
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader


class ModelMarkdownParser:
    """Parser for FAIRFluids model.md file"""
    
    def __init__(self, markdown_file: str):
        self.markdown_file = markdown_file
        self.content = ""
        self.classes = []
        self.enums = []
        
    def read_file(self):
        """Read the markdown file"""
        with open(self.markdown_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def parse_classes(self) -> List[Dict[str, Any]]:
        """Parse classes from the markdown content"""
        classes = []
        
        # Split content at "## Enumerations" to get only the classes section
        parts = self.content.split('## Enumerations')
        if len(parts) < 2:
            print("Warning: Could not find '## Enumerations' section")
            return classes
            
        classes_content = parts[0]
        
        # Split content into sections
        sections = classes_content.split('### ')
        
        for section in sections:
            if not section.strip():
                continue
                
            lines = section.strip().split('\n')
            if not lines:
                continue
                
            # Check if this is a class (not an enum)
            class_name = lines[0].strip()
            
            # Skip if it's a general section header or empty
            if class_name in ['', 'General information']:
                continue
                
            # This is a class, parse its fields
            fields = self._parse_class_fields(lines[1:])
            if fields:
                classes.append({
                    "name": class_name,
                    "fields": fields
                })
        
        return classes
    
    def _parse_class_fields(self, lines: List[str]) -> List[Dict[str, str]]:
        """Parse fields from class lines"""
        fields = []
        current_field = None
        for line in lines:
            line = line.rstrip()
            if not line:
                continue
            # Field definition: - field_name
            if re.match(r'^- \w+', line):
                # Save previous field if exists
                if current_field:
                    fields.append(current_field)
                # Start new field
                field_name = line[2:].split()[0]
                current_field = {
                    "name": field_name,
                    "type": "",
                    "description": ""
                }
            elif current_field and re.match(r'^\s*- Type:', line):
                # Type on indented line
                type_val = line.split(':', 1)[1].strip()
                # Convert 'integer' to 'int' and 'Identifier' to 'int'
                if type_val == 'integer' or type_val == 'Identifier':
                    type_val = 'int'
                current_field["type"] = type_val
            elif current_field and re.match(r'^\s*- Description:', line):
                # Description on indented line
                desc_val = line.split(':', 1)[1].strip()
                current_field["description"] = desc_val
        # Add the last field
        if current_field:
            fields.append(current_field)
        # Remove any fields named 'Type' or 'Description'
        fields = [f for f in fields if f['name'].lower() not in ['type', 'description']]
        return fields
    
    def parse_enums(self) -> List[Dict[str, Any]]:
        """Parse enums from the markdown content"""
        enums = []
        
        # Split content at "## Enumerations" to get only the enums section
        parts = self.content.split('## Enumerations')
        if len(parts) < 2:
            print("Warning: Could not find '## Enumerations' section")
            return enums
            
        enums_content = parts[1]
        
        # Find enum sections - match any word after ### that has a Python code block
        enum_pattern = r'### (\w+)\s*\n\s*```python\s*\n(.*?)\n\s*```'
        enum_matches = re.findall(enum_pattern, enums_content, re.DOTALL)
        
        for enum_name, enum_content in enum_matches:
            values = self._parse_enum_values(enum_content)
            if values:
                enums.append({
                    "name": enum_name,
                    "enum_values": values
                })
        
        return enums
    
    def _parse_enum_values(self, enum_content: str) -> List[str]:
        """Parse enum values from the content"""
        values = []
        
        # Extract values from lines like: VALUE = 'value'
        value_pattern = r'(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'
        matches = re.findall(value_pattern, enum_content)
        
        for value_name, value_string in matches:
            values.append(value_name)
        
        return values
    
    def parse(self) -> Dict[str, Any]:
        """Parse the entire markdown file"""
        self.read_file()
        
        self.classes = self.parse_classes()
        self.enums = self.parse_enums()
        
        return {
            "classes": self.classes,
            "enums": self.enums
        }


def generate_baml_from_markdown(markdown_file: str, template_file: str, output_file: str):
    """Generate BAML file from markdown using Jinja template"""
    
    # Parse the markdown file
    parser = ModelMarkdownParser(markdown_file)
    parsed_data = parser.parse()
    
    print(f"Parsed {len(parsed_data['classes'])} classes:")
    for cls in parsed_data['classes']:
        print(f"  - {cls['name']} ({len(cls['fields'])} fields)")
    
    print(f"Parsed {len(parsed_data['enums'])} enums:")
    for enum in parsed_data['enums']:
        print(f"  - {enum['name']} ({len(enum['enum_values'])} values)")
    
    # Load and render Jinja template
    env = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template(template_file)
    
    output = template.render(**parsed_data)
    
    # Write output file
    with open(output_file, "w") as f:
        f.write(output)
    
    print(f"✅ BAML model generated: {output_file}")


if __name__ == "__main__":
    # Generate BAML from the model.md file
    generate_baml_from_markdown(
        markdown_file="FAIRFluids/specifications/model.md",
        template_file="jinja/md_to_baml.j2",
        output_file="jinja/generated_model.baml"
    )