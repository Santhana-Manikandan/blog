from fastapi import FastAPI, Form, Query
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "backend/likes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blogs (
            id INTEGER PRIMARY KEY,
            likes INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

@app.post("/like")
async def like_unlike(blog_id: str = Form(...), action: str = Form(...)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get current likes
    cursor.execute("SELECT likes FROM blogs WHERE id = ?", (blog_id,))
    row = cursor.fetchone()

    if row:
        current_likes = row[0]
        if action == "like":
            new_likes = current_likes + 1
        elif action == "unlike":
            new_likes = max(current_likes - 1, 0)  # don't go below 0
        else:
            conn.close()
            return JSONResponse(content={"error": "Invalid action"}, status_code=400)

        cursor.execute("UPDATE blogs SET likes = ? WHERE id = ?", (new_likes, blog_id))
    else:
        # Create blog only if action is 'like'
        if action == "like":
            new_likes = 1
            cursor.execute("INSERT INTO blogs (id, likes) VALUES (?, ?)", (blog_id, new_likes))
        else:
            conn.close()
            return JSONResponse(content={"error": "Blog not found"}, status_code=404)

    conn.commit()
    conn.close()

    return JSONResponse(content={"blog_id": blog_id, "likes": new_likes})


@app.get("/like")
async def get_likes(blog_id: str = Query(None)):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if blog_id:
        # Return likes for a specific blog
        cursor.execute("SELECT likes FROM blogs WHERE id = ?", (blog_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {"blog_id": blog_id, "likes": row[0]}
        else:
            return {"blog_id": blog_id, "likes": 0}
    else:
        # Return all blogs and their likes
        cursor.execute("SELECT id, likes FROM blogs")
        rows = cursor.fetchall()
        conn.close()

        return {"likes": {blog_id: like for blog_id, like in rows}}
