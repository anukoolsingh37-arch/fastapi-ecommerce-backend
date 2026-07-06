import urllib.request, re

# Get the store page HTML
r = urllib.request.urlopen('http://localhost:8000/store')
html = r.read().decode('utf-8')

# Find the products container - check the script section for the renderProducts calls
# Also check if img tags in product cards have proper URLs
# Let's look at what the /products/search endpoint returns as the raw JSON
r2 = urllib.request.urlopen('http://localhost:8000/products/search')
raw = r2.read().decode('utf-8')
print("First 2000 chars of products/search response:")
print(raw[:2000])
print("\n---")
print("Does store HTML contain 'Failed to fetch'?", 'Failed to fetch' in html)
print("Does store HTML contain 'Error' in context?", 'Unable to load product' in html)