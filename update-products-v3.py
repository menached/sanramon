import openai
import html
import re
import os
import ssl
import nltk
import requests
if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt', quiet=True)
credentials = {}
creds_file_path = os.path.join(
          os.path.dirname(os.path.abspath(__file__)),
          "../creds.txt"
          )
with open(creds_file_path) as f:
    current_section = None
    for line in f:
        line = line.strip()
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
        elif current_section == "sanramon.doap.com":
            key, value = line.split(" = ")
            credentials[key] = value
openai.api_key = credentials["openai.api_key"]
auth = (
    credentials["sanramon.doap.com_consumer_key"],
    credentials["sanramon.doap.com_consumer_secret"]
    )
base_url = "https://sanramon.doap.com/wp-json/wc/v3/products"
counter = 0
page = 1
while True:
    response = requests.get(f'{base_url}?page={page}&per_page=10', auth=auth)  # Modify URL to include per_page=3
    response.raise_for_status()
    products = response.json()
    if not products:
        break
    for product in products:
        # Use OpenAI API to generate new product name
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
                {"role": "system", "content": "You are a helpful budtender who knows all about the cannabis industry."},
                {"role": "user", "content": f"I have a product named '{product['name']}' with a short description of '{product['short_description']}' and a long description of '{product['description']}'. I need a new but similar name for this product that will both help with SEO and improve the product visibility in search engines.  Dont stray too far from the core idea of the original description. Use the word Doap as an acronmy for awesome. Limit the title to abut 70 characters.  Do not use any punctuation or apostrophes or quotes. Keep it short and simple and best optimized for SEO.  Also generate a new short_description and description that follows what is already in name, short_description, and description but is more concise, optimized for SEO, and unique. Mention landmarks in the San Ramon area in the descriptions.  Especially good meet up spots. "},
            ]
        )
        
        new_product_name = response['choices'][0]['message']['content'].strip()
        new_short_description = response['choices'][0]['message']['content'].split("\n\n")[1]
        new_description = response['choices'][0]['message']['content'].split("\n\n")[2]

        print("\nResponse: ", response)
        print()
        print("\nNew Product Name: ", new_product_name)
        print()
        replacements = ['<br>', '<br />', '<p>', '</p>', '<h5>', '</h5>', '\n', '"', "'", "New Description:", "New Short Description"]
        for rep in replacements:
            product['name'] = product['name'].replace(rep, '')
            old_product_name = product['name']
            old_short_description = product['short_description']
            old_description = product['description']
            product['short_description'] = html.unescape(product['short_description'].replace(rep, ''))
            product['description'] = html.unescape(product['description'].replace(rep, ''))
            new_product_name = html.unescape(new_product_name.replace(rep, ''))
            new_short_description = html.unescape(new_short_description.replace(rep, ''))
            new_description = html.unescape(new_description.replace(rep, ''))

        # Adding ' - SALE' from product name
        # product['name'] += ' - SALE'
        counter = counter + 1
        print(
                f'ID: {product["id"]}  '
                f'\nSku: {product["sku"]}  '
                f'\nPermalink: {product["permalink"]}'
                f'\nCurrent Name: {old_product_name}  '
                f'\nProposed New Name: {new_product_name}  '
                f'\nCurrent Short Description: {product["short_description"]}  '
                f'\nProposed Short Description: {new_short_description}  '
                f'\nCurrent Description: {product["description"]}  '
                f'\nProposed Description: {new_description}  '
                f'\n'
                )
        # Uncomment the next three lines to update products. 
        # update_url = f'{base_url}/{product["id"]}'
        # update_response = requests.put(update_url, json=product, auth=auth)
        # update_response.raise_for_status

    page += 1

print("Product found: ", counter)
