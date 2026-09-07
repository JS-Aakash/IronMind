import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import asyncio
from services.rag.service import RagService

async def reindex():
    index_file = Path("storage/knowledge/vector_index.json")
    if index_file.exists():
        index_file.write_text(json.dumps({"chunks": []}), encoding="utf-8")
        print("Reset vector_index.json to empty.")

    rag = RagService()
    print(f"Seed knowledge initialized. Document count: {len(rag.list_documents())}")

    # Add the authentic txt files in storage/knowledge if not indexed yet
    txt_files = [
        ("doc_mrpl_sop_mech_4_2", "MRPL_SOP_MECH_4_2_Vibration_Overhaul.txt", "SOP", "MRPL SOP MECH 4.2 Centrifugal Pump Vibration & Overhaul"),
        ("doc_mrpl_esd101", "MRPL_ESD101_Safety_Standard.txt", "Safety Standard", "MRPL ESD-101 Valve Safety Standard"),
        ("doc_mrpl_flaring", "MRPL_Flaring_Manual.txt", "Environmental Standard", "MRPL Flaring Manual"),
    ]

    for doc_id, filename, category, title in txt_files:
        p = Path("storage/knowledge") / filename
        if p.exists():
            content = p.read_text(encoding="utf-8")
            chunks = rag.chunker.chunk_document_pages(
                document_id=doc_id,
                document_name=filename,
                pages=[(1, content)]
            )
            rag._embed_and_index_chunks_sync(chunks)
            print(f"Indexed {len(chunks)} chunks for {filename}")

    # Verify search query
    query = "vibration velocity thresholds pump P-101 SOP Section 4.2"
    result = await rag.search(query=query, top_k=3)
    print(f"\nSearch test for '{query}':")
    for r in result.chunks:
        print(f" - [{r.document_name}] Score: {r.score:.4f} Text: {r.text[:100]}...")

if __name__ == "__main__":
    asyncio.run(reindex())
