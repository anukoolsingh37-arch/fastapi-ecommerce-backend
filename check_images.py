import urllib.request, json

# Check what products API returns
d = json.loads(urllib.request.urlopen('http://localhost:8000/products/search').read())
for p in d[:3]:
    img = p.get('image')
    print(f"ID={p['id']}, title={p['title']}, image={repr(img)[:80] if img else 'NONE'}")
print(f"Total: {len(d)} products")