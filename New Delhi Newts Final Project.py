#C:\Users\khanj\OneDrive\Desktop\New folder\PMA.jpg
#C:\Users\khanj\OneDrive\Desktop\New folder\EER.jpg

import cv2
import pytesseract
import requests
from bs4 import BeautifulSoup
import webbrowser
import tempfile
import re

# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Update this path

# Base URL for UT Austin
base_url = "https://utdirect.utexas.edu"

# URL of Buildings
url = f"{base_url}/apps/campus/buildings/nlogon/facilities/"

# Fetch the main webpage content
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Dictionary to store building data (acronym/full name -> individual page URL)
buildinglinks = {}

# Locate the table body containing building information
table_body = soup.find('tbody')

# Extract building links and names
for row in table_body.find_all('tr'):
    header_cell = row.find('th')
    cells = row.find_all('td')
    if header_cell and len(cells) >= 1:
        acronym_link = header_cell.find('a')
        if acronym_link:
            acronym = acronym_link.text.strip()
            building_name = cells[0].text.strip()
            building_page_url = f"{base_url}{acronym_link['href']}"

            # Store the link for both acronym and building name
            buildinglinks[acronym.upper()] = {"url": building_page_url, "name": building_name}
            buildinglinks[building_name.upper()] = {"url": building_page_url, "name": building_name}

# Normalize text for consistent comparison
def normalize_text(text):
    # Replace "&" with "and", remove commas, and normalize spaces
    normalized = text.replace("&", "and").replace(",", "").strip()
    normalized = re.sub(r'\s+', ' ', normalized)  # Remove extra spaces
    return normalized.upper()

# OCR function to extract text from an image
def perform_ocr_on_image(image_path):
    # Read the image
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Unable to read the image. Please check the file path.")
        return None

    # Convert image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Use Tesseract OCR to extract text
    extract_text = pytesseract.image_to_string(gray_image)

    # Remove special characters and numbers
    filtered_text = re.sub(r'[^A-Za-z\s&]', '', extract_text)

    return filtered_text.strip()

# Get address and map URL from a building's page
def get_building_info(building_page_url):
    response = requests.get(building_page_url)
    building_soup = BeautifulSoup(response.content, 'html.parser')

    # Extract the address
    address_tag = building_soup.find('h3', string=lambda t: t and ',' in t)
    if not address_tag:
        address_tag = building_soup.find('h3')
    address = address_tag.get_text(strip=True) if address_tag else "Address not found."

    # Extract the map URL
    iframe_tag = building_soup.find('iframe')
    map_url = iframe_tag['src'] if iframe_tag else "Map not found."

    return address, map_url

# Generate and open the HTML file
def generate_html_and_open(building_name, building_acronym, address, map_url):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Campus Location</title>
    </head>
    <body>
        <h1 style="text-align: center;">
            You are currently located at the {building_name} ({building_acronym})
        </h1>
        <p style="text-align: center;">Address: {address}</p>
        <div style="text-align: center;">
            <iframe
                src="{map_url}"
                width="600"
                height="450"
                style="border:0; display: block; margin: 0 auto;"
                allowfullscreen=""
                loading="lazy"
                referrerpolicy="no-referrer-when-downgrade">
            </iframe>
        </div>
    </body>
    </html>
    """
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".html") as temp_file:
        temp_file.write(html_content)
        webbrowser.open(f"file://{temp_file.name}")

# Locate the building and generate HTML
def get_building_location(filtered_text):
    normalized_input = normalize_text(filtered_text)

    # Match detected text to building directory
    for key, building_info in buildinglinks.items():
        normalized_building_name = normalize_text(building_info["name"])
        if normalized_input == normalized_building_name or normalized_input == key:
            address, map_url = get_building_info(building_info["url"])
            if address != "Address not found." and map_url != "Map not found.":
                # Output the match before generating HTML
                print(f"Match found: {building_info['name']} ({key})")
                generate_html_and_open(building_info["name"], key, address, map_url)
            else:
                print("Unable to retrieve full information for the building.")
            return

    print("Building not found. Please check your input.")

# Main function
if __name__ == "__main__":
    # Prompt the user for the image file path
    image_path = input("Please enter the full path to the image file: ")

    # Perform OCR
    detected_text = perform_ocr_on_image(image_path)

    if detected_text:
        get_building_location(detected_text)
    else:
        print("No text detected in the image.")

