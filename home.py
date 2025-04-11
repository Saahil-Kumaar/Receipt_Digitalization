import easyocr
import re
import streamlit as st
from PIL import Image

def categorize_receipt_data(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)  # Extract text only (no bounding boxes)

    data = {
        "merchant": "",
        "products": [],
        "prices": [],
        "total": "",
        "date": ""
    }

    merchant_found = False
    product_list = []  # Temporary storage for product-price pairing
    possible_totals = []

    for line in result:
        line = line.strip()

        # Identify Merchant Name (Usually the first meaningful line)
        if not merchant_found and len(line) > 3:
            data["merchant"] = line
            merchant_found = True
            continue

        # Identify Prices (Regex: $9.99, 12.50, etc.)
        # prices = re.findall(r'\d+\.\d{2}', line)
        # if prices:
        #     if "SUB TOTAL" in line.upper():  # Detect total price
        #         data["total"] = prices[-1] if prices else ""
        #     # elif "SUB TOTAL" in line.upper():  # Detect subtotal price
        #     #     data["total"] = prices[-1] if prices else ""
        #     else:
        #         product_list.append((line, prices[-1]))  # Store product-price pair
        #     continue


        prices = re.findall(r'\d+\.\d{2}', line)
        if prices:
            price_value = prices[-1]  # Get last detected price in the line

            # Check if this line likely contains the total amount
            if re.search(r'TOTAL|SUBTOTAL|GRAND TOTAL|SUB TOTAL', line, re.IGNORECASE):
                data["total"] = price_value  # Store as total
                continue  # Skip adding it to product list

            product_list.append((line, price_value))  # Store product-price pair
            possible_totals.append(float(price_value))  # Store potential total prices
            continue

        # Identify Dates (Format: MM/DD/YYYY or DD/MM/YYYY)
        if re.search(r'\d{1,2}/\d{1,2}/\d{2,4}', line):
            data["date"] = line
            continue

        # Assume remaining lines as product names
        if any(char.isalpha() for char in line) and len(line) > 2:
            product_list.append((line, ""))  # Store product without price for now

    # Match products with prices
    for i in range(len(product_list)):
        product, price = product_list[i]
        if not price and i + 1 < len(product_list) and product_list[i + 1][1]:
            price = product_list[i + 1][1]  # Assign price from the next line if missing
        data["products"].append({"name": product, "price": price})

    return data

# Streamlit UI
st.title("Receipt Digitalization with EasyOCR 🧾")

uploaded_file = st.file_uploader("Upload a receipt image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # Display uploaded image
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Receipt", use_container_width=True)

    # Save image temporarily
    image_path = "temp_receipt.jpg"
    image.save(image_path)

    # Process receipt
    receipt_data = categorize_receipt_data(image_path)

    # Display results
    st.subheader("Extracted Information:")
    col1, col2 = st.columns(2)
    query1 = col1.text_input("**Merchant Name**:", receipt_data['merchant'])
    query2 = col1.text_input("**Date**:", receipt_data['date'])
    query3 = col1.text_input("**Total Amount**:", receipt_data['total'])
    # st.write(f"**Merchant:** {receipt_data['merchant']}")
    # st.write(f"**Date:** {receipt_data['date']}")

    if receipt_data['products']:
        st.subheader("Products & Prices:")
        for item in receipt_data["products"]:
            if item['price'] and isinstance(item['name'], float)!=True:
                st.write(f"- {item['name']}: ${item['price']}")

    st.write(f"**Total Amount:** ${receipt_data['total']}")