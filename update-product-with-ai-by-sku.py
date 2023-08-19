import openai
import sys
import html
import re
import os
import ssl
import nltk
import requests
from PIL import Image
import pprint


if not nltk.data.find('tokenizers/punkt'):
    nltk.download('punkt', quiet=True)

sku = sys.argv[1]

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

# returning the URL of one image as
# we are generating only one image
def generate(new_pics_prompt):
    res = openai.Image.create(
        # text describing the generated image
        prompt=new_pics_prompt,
        # number of images to generate
        n=2,
        # size of each generated image
        size="1024x1024",
    )
    return res["data"][0]["url"]



base_url = "https://sanramon.doap.com/wp-json/wc/v3/products"

response = requests.get(f'{base_url}', auth=auth, params={'sku': sku})
response.raise_for_status()

if not response.json():
    print(f"No product found with SKU: {sku}")
    exit()

product = response.json()[0]

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages = [
    {
        "role": "system",
        "content": "You are a helpful budtender who knows all about the cannabis industry.",
    },
    {
        "role": "user",
        "content": f"I have a product with SKU '{sku}' named '{product['name']}' with a short description of '{product['short_description']}' and a long description of '{product['description']}'. "
                   f"I need a new but similar name for this product that will both help with SEO and improve the product visibility in search engines. "
                   f"Don't stray too far from the core idea of the original description. Use the word Doap as an acronym for awesome. "
                   f"Limit the new product name to about 70 characters.  Do not use any punctuation or apostrophes or quotes. "
                   f"Do use proper capitalization. Optimize all for SEO.   "
                   f"Never spell the word dope, always substitute doap."
                   f"If its greenhouse flower mention the farms of San Ramon sourced locally grown organic flower."
    },
]
)

new_product_name = response['choices'][0]['message']['content'].strip()
new_product_name = html.unescape(re.sub('<.*?>', '', new_product_name))

response_short_description = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages = [
    {
        "role": "system",
        "content": "You are a knowledgeable and creative budtender with a way with words. You are skilled in creating captivating descriptions for cannabis products.",
    },
    {
        "role": "user",
        "content": f"I have a product with SKU '{sku}' named '{new_product_name}' with a short description '{product['short_description']}' and description '{product['description']}'. "
                   f"I need a new but similar short description that will both help with SEO and improve the product visibility in search engines."
                   f"Limit the new short description to about 160 characters."
                   f"Optimize for SEO and make sure it is not detectable by AI detectors. "
                   f"Having a slightly hippie kind of vibe is cool. "
                   f"Doap is a synonym for awesome."
                   f"Make sure it is not detectable by AI detectors. "
                   f"Having a hippie kind of vibe is cool. "
                   f"If its greenhouse flower mention the farms of San Ramon sourced locally grown organic flower."
                   f"Don't mention price anywhere."
    },
]
)

new_short_description = response_short_description['choices'][0]['message']['content'].strip()
new_short_description = html.unescape(re.sub('<.*?>', '', new_short_description))

response_long_description = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages = [
    {
        "role": "system",
        "content": "You are a knowledgeable and creative budtender with a way with words. You are skilled in creating engaging and detailed descriptions for cannabis products.",
    },
    {
        "role": "user",
        "content": f"I have a product with SKU '{sku}' named '{new_product_name}' with a long description ' {product['description']}'. "
                   f"I need a new but similar long description that will both help with SEO and improve the product visibility in search engines. "
                   f"The new description should be detailed and captivating to pique the interest of potential customers. "
                   f"Optimize for SEO and make sure it is not detectable by AI detectors."
                   f"Mention landmarks in the San Ramon area "
                   f"and don't mention price anywhere. "
                   f"Having a slightly hippie kind of vibe is cool. "
                   f"Come up with and casually mention a few landmarks that are convenient for quickly meeting up that are well-known, well-traveled in the San Ramon area. "
                   f"Casually mention we could meet you at one of these locations or deliver directly to your home or work. "
                   f"If its greenhouse flower mention the farms of San Ramon sourced locally grown organic flower."
                   f"Mention we accept cash, credit, crypto, applepay, zelle, paypal, venmo and others"
                   f"Limit the new description to about 900 characters."
    },
]
)

new_long_description = response_long_description['choices'][0]['message']['content'].strip()
new_long_description = html.unescape(re.sub('<.*?>', '', new_long_description))

old_product_name = product['name']
product['name'] = new_product_name
old_short_description = product['short_description']
product['short_description'] = new_short_description

old_long_description = product['description']
product['description'] = new_long_description

new_pic_prompt = "Create a picture of cannabis growing in a field"
# Get the image URL from OpenAI
new_image_url = generate(new_pic_prompt)

# Update the product images with the new image
for image in product['images']:
    del image['id']
    del image['date_created']
    del image['date_created_gmt']
    del image['date_modified']
    del image['date_modified_gmt']

    old_image_url = image['src']
    image['src'] = new_image_url
    image['name'] = new_product_name

    print(f"Old Image URL: {old_image_url}")
    print(f"New Image URL: {new_image_url}\n")



print(
    f"SKU: {sku}\n\n"
    f"Old name:\n{old_product_name}\n"
    f"Old short_description:\n{old_short_description}\n"
    f"Old description:\n{old_long_description}\n"
    f"New name:\n{new_product_name}\n"
    f"New short_description:\n{new_short_description}\n"
    # f"New description:\n{new_long_description}"
)

pprint.pprint (product)

# Update the product with the new name
update_url = f'{base_url}/{product["id"]}'
update_response = requests.put(update_url, json=product, auth=auth)
update_response.raise_for_status()


#proceed = input("Do you want to proceed with updating the product? (Yes/No): ")
#proceed = proceed.lower().strip()  # Make sure the response is in lowercase and stripped of any leading/trailing spaces

#if proceed == 'yes':
#    update_response = requests.put(update_url, json=product, auth=auth)
#    update_response.raise_for_status()
#    print()
#else:
#    print("Operation cancelled by the user.")
