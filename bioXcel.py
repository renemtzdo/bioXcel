import webbrowser, os
import json
import boto3
import io
from io import BytesIO
import sys
from pprint import pprint
import openai
from reportlab.pdfgen import canvas

## Code taken from AWS's Textraxt API documentation. Using OCR tech, transcribing an image into text and then into table format.
def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result['Relationships']:
        if relationship['Type'] == 'CHILD':
            for child_id in relationship['Ids']:
                cell = blocks_map[child_id]
                if cell['BlockType'] == 'CELL':
                    row_index = cell['RowIndex']
                    col_index = cell['ColumnIndex']
                    if row_index not in rows:
                        rows[row_index] = {}
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] =='SELECTED':
                            text +=  'X '    
    return text


def get_table_csv_results(file_name):

    with open(file_name, 'rb') as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
        print('Image loaded', file_name)

    # Insert AWS profile name below
    session = boto3.Session(profile_name='INSERT PROFILE NAME')
    # Insert AWS region name below. Default is us-east-1
    client = session.client('textract', region_name='us-east-1')
    response = client.analyze_document(Document={'Bytes': bytes_test}, FeatureTypes=['TABLES'])

    blocks=response['Blocks']
    pprint(blocks)

    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block['Id']] = block
        if block['BlockType'] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        return "<b> NO Table FOUND </b>"

    csv = ''
    for index, table in enumerate(table_blocks):
        csv += generate_table_csv(table, blocks_map, index +1)
        csv += '\n\n'

    return csv

def generate_table_csv(table_result, blocks_map, table_index):
    rows = get_rows_columns_map(table_result, blocks_map)

    table_id = 'Table_' + str(table_index)
    
    csv = 'Table: {0}\n\n'.format(table_id)

    for row_index, cols in rows.items():
        
        for col_index, text in cols.items():
            csv += '{}'.format(text) + ","
        csv += '\n'
        
    csv += '\n\n\n'
    return csv

def main(file_name):
    table_csv = get_table_csv_results(file_name)
    #INSERT OUTPUT file name
    output_file = 'output.csv'

    with open(output_file, "wt") as fout:
        fout.write(table_csv)

if __name__ == "__main__":
    file_name = sys.argv[1]
    main(file_name)
#Some code below taken from OPENAI's API documentation.

#Insert API Key below
openai.api_key = 'INSERT API KEY'

def chat_with_gpt(prompt, table_data):
    prompt_with_data = f"{prompt}\n{table_data}"
    response = openai.Completion.create(
    #Insert OPENAI engien, default is text-davinci-003
        engine='text-davinci-003',
        prompt=prompt_with_data,
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.2,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )

    return response.choices[0].text.strip()

table_data = get_table_csv_results(file_name)

#Insert Personalized prompt for OPENAI-gpt below. Default is:
prompt = "Summarize the table with summary statistics and explain any variable relationships."

response = chat_with_gpt(prompt, table_data)

def string_to_txt(text, output_file):
    with open(output_file, "w") as file:
        file.write(text)

output_file = "output.txt"
string_to_txt(response, output_file)

