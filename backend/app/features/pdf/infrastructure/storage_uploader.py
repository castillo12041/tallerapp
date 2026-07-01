from __future__ import annotations

import uuid
from urllib.parse import quote

from app.features.pdf.domain.entities import PdfDocument


class FirebaseStorageUploader:
    """
    Sube PDFs a Firebase Storage y retorna una URL de descarga con token persistente.

    La URL usa el formato nativo de Firebase Storage con `?alt=media&token=<uuid>`.
    No expira y no requiere autenticación adicional, pero el token es opaco y difícil
    de adivinar. Para mayor seguridad en producción, rotar el token al revocar acceso.
    """

    def __init__(self, bucket_name: str) -> None:
        self._bucket_name = bucket_name

    def upload(
        self,
        doc: PdfDocument,
        tenant_id: str,
        inspection_id: str,
    ) -> str:
        from firebase_admin import storage as fb_storage  # lazy — no disponible en tests

        bucket = fb_storage.bucket(name=self._bucket_name)
        blob_path = f"reports/{tenant_id}/{inspection_id}/{doc.filename}"
        blob = bucket.blob(blob_path)

        download_token = str(uuid.uuid4())
        blob.metadata = {"firebaseStorageDownloadTokens": download_token}
        blob.upload_from_string(doc.content, content_type=doc.content_type)
        blob.patch()

        encoded_path = quote(blob_path, safe="")
        return (
            f"https://firebasestorage.googleapis.com/v0/b/{self._bucket_name}"
            f"/o/{encoded_path}?alt=media&token={download_token}"
        )
