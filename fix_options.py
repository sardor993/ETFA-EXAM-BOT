import json
import re

# JSON faylni o'qish
with open('questions_aviation_general.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Har bir savol uchun options dan A), B), C), D) harflarini olib tashlash
for question in data:
    if 'options' in question:
        # Har bir option dan boshidagi harf va ) ni olib tashlash
        cleaned_options = []
        for option in question['options']:
            # A), B), C), D) ni olib tashlash
            cleaned = re.sub(r'^[A-D]\)\s*', '', option)
            cleaned_options.append(cleaned)
        question['options'] = cleaned_options

# Tuzatilgan ma'lumotlarni qayta yozish
with open('questions_aviation_general.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Faylda A), B), C), D) harflari olib tashlandi!")