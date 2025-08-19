import os
import pandas as pd

def infer_field_type(dtype):
    if pd.api.types.is_numeric_dtype(dtype):
        return 'numerical'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'datetime'
    elif pd.api.types.is_string_dtype(dtype):
        return 'categorical'
    else:
        return 'unknown'

class SchemaParsingAgent:
    def __init__(self, file_path):
        self.file_path = file_path
        self.table_name = os.path.splitext(os.path.basename(file_path))[0]
        self.dataframe = self._load_data()
        self.schema = None

    def _load_data(self):
        ext = os.path.splitext(self.file_path)[-1].lower()
        if ext == '.csv':
            return pd.read_csv(self.file_path)
        elif ext in ('.xls', '.xlsx'):
            return pd.read_excel(self.file_path)
        else:
            raise ValueError(f'Unsupported file extension: {ext}')

    def parse_schema(self):
        self.schema = []
        for col in self.dataframe.columns:
            dtype = self.dataframe[col].dtype
            semantic_type = infer_field_type(dtype)
            # include the table name in each field dictionary
            self.schema.append({
                'table_name': self.table_name,   # added table_name here
                'field_name': col,
                'dtype': str(dtype),
                'semantic_type': semantic_type
            }) 
    def annotate_schema(self):
        for field in self.schema:
            name = field['field_name']
            if name.lower() == 'id' or name.lower().endswith('_id'):
                field['role'] = 'identifier'
            elif field['semantic_type'] == 'numerical':
                field['role'] = 'metric'
            else:
                field['role'] = 'dimension'

    def get_schema(self):
        return self.schema

    def schema_api(self):
        def get_fields_by_role(role):
            return [f['field_name'] for f in self.schema if f.get('role') == role]
        return {
            'all_fields': [f['field_name'] for f in self.schema],
            'metrics': get_fields_by_role('metric'),
            'dimensions': get_fields_by_role('dimension'),
            'identifiers': get_fields_by_role('identifier')
        }

# Usage Example

if __name__ == '__main__':
    file_path = 'file path'      # Or 'your_data.xlsx'
    agent = SchemaParsingAgent(file_path)
    agent.parse_schema()
    agent.annotate_schema()
    print(agent.get_schema())
    print(agent.schema_api())
