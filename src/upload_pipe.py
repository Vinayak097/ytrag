from script_download import prints ,Transcript
from chunks import process_transcripts
from embed import process_chunks
from qdrant import upload_embeddings
prints()

Transcript()
print("transcript done ")

process_transcripts()
print("chunks done ")
process_chunks()
print("chunks done ")
upload_embeddings()
print("upload done ")











