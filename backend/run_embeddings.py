from database import SessionLocal
from models import Artwork
from routers.ai import compute_and_store_embedding
from pathlib import Path

db = SessionLocal()
artworks = db.query(Artwork).filter(Artwork.embedding == None).all()

print(f"Computing embeddings for {len(artworks)} artworks...")
for art in artworks:
    if art.image_urls:
        img_url = art.image_urls[0]
        img_path = "uploads/artworks/" + img_url.split("/")[-1]
        print(f"  Trying path: {img_path}")
        if Path(img_path).exists():
            print(f"  Processing: {art.title}")
            compute_and_store_embedding(art.id, img_path, db)
        else:
            print(f"  File not found: {img_path}")

print("Done!")
db.close()