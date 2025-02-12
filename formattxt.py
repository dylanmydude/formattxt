import os
import pandas as pd
import re

# Directory containing the files
FILES_DIR = "files"

# Ensure 'files/' directory exists
if not os.path.exists(FILES_DIR):
    raise FileNotFoundError(f"Directory '{FILES_DIR}' not found!")

def clean_txt_file(filename):
    input_file = os.path.join(FILES_DIR, filename)
    output_file = os.path.join(FILES_DIR, f"cleaned_{filename}")

    # Extract Device Name from filename (e.g., "EMAP_312.txt" -> "EMAP_312")
    device_name = os.path.splitext(filename)[0]  # Remove file extension

    # Read the file line by line
    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Extract Device ID from DevEui= and remove all spaces
    device_id = ""
    for line in lines:
        if "DevEui=" in line:
            device_id = line.split("=")[-1].strip().replace(" ", "")  # Remove spaces
            break  # Stop after finding the first occurrence

    # Find the header row dynamically
    header_keywords = ["Stop", "Tx", "events", "when", "read", "sensor", "data"]
    header_index = None

    for i, line in enumerate(lines):
        if all(keyword in line for keyword in header_keywords):
            header_index = i
            break

    if header_index is None:
        print(f"⚠️ Skipping file '{filename}': Header row not found.")
        return

    # Extract only the relevant data after the detected header
    data_lines = lines[header_index + 1:]

    # Remove blank rows
    data_lines = [line.strip() for line in data_lines if line.strip()]

    # Extract structured data using regex (keeping only Date, Time, Temperature, and Humidity)
    pattern = re.compile(r"(\d+)\s+([\d/]+)\s+([\d:]+)\s+\d+\s+\d+\s+sht_temp=([\d.]+)\s+sht_hum=([\d.]+)")

    structured_data = [pattern.match(line) for line in data_lines]
    structured_data = [match.groups() for match in structured_data if match]

    # Convert to DataFrame
    df = pd.DataFrame(structured_data, columns=["Tx", "Date", "Time", "Temperature", "Humidity"])

    # Convert Date & Time into a proper format
    df["Received At"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%Y/%m/%d %H:%M:%S")

    # Floor time to nearest 5-minute interval
    df["Received At"] = df["Received At"].dt.floor("5min")

    # Determine the cutoff timestamp (28th at 00:00:00)
    cutoff_datetime = pd.Timestamp(df["Received At"].dt.year.iloc[0], 1, 28, 0, 0, 0)

    # Keep all rows before OR equal to `28th at 00:00`
    df = df[df["Received At"] <= cutoff_datetime]

    # Add Device ID (without spaces) and extracted Device Name
    df.insert(0, "Device ID", device_id)
    df.insert(1, "Device Name", device_name)

    # Keep only the necessary columns
    df = df[["Device ID", "Device Name", "Received At", "Temperature", "Humidity"]]

    # Save cleaned data
    df.to_csv(output_file, index=False, sep=" ", encoding="utf-8")

    print(f"✅ Cleaned file saved as: {output_file}")

# Process all .txt files in the folder
for file in os.listdir(FILES_DIR):
    if file.endswith(".txt"):
        print(f"\n🔄 Processing {file}...")
        clean_txt_file(file)

print("\n🎉 All files processed successfully!")
