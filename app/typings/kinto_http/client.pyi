"""
This type stub file was generated by pyright.
"""

from contextlib import contextmanager
from typing import Dict, List

logger = ...
retry_timeout = ...

class Client:
    def __init__(
        self,
        *,
        server_url=...,
        session=...,
        auth=...,
        bucket=...,
        collection=...,
        retry=...,
        retry_after=...,
        timeout=...,
        ignore_batch_4xx=...,
        headers=...
    ) -> None: ...
    def clone(self, **kwargs): ...
    @retry_timeout
    @contextmanager
    def batch(self, **kwargs): ...
    def get_endpoint(self, name, *, bucket=..., group=..., collection=..., id=...) -> str:
        """Return the endpoint with named parameters."""
        ...
    @retry_timeout
    def server_info(self) -> Dict: ...
    @retry_timeout
    def create_bucket(
        self, *, id=..., data=..., permissions=..., safe=..., if_not_exists=...
    ) -> Dict: ...
    @retry_timeout
    def update_bucket(
        self, *, id=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    @retry_timeout
    def patch_bucket(
        self,
        *,
        id=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict:
        """Issue a PATCH request on a bucket.

        :param changes: the patch to apply
        :type changes: PatchType
        :param original: the original bucket, from which the ID and
            last_modified can be taken
        :type original: dict
        """
        ...
    def get_buckets(self, **kwargs) -> List[Dict]: ...
    @retry_timeout
    def get_bucket(self, *, id=..., **kwargs) -> Dict: ...
    @retry_timeout
    def delete_bucket(self, *, id=..., safe=..., if_match=..., if_exists=...) -> Dict: ...
    @retry_timeout
    def delete_buckets(self, *, safe=..., if_match=...) -> Dict: ...
    def get_groups(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    @retry_timeout
    def create_group(
        self,
        *,
        id=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    @retry_timeout
    def update_group(
        self, *, id=..., bucket=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    @retry_timeout
    def patch_group(
        self,
        *,
        id=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict:
        """Issue a PATCH request on a bucket.

        :param changes: the patch to apply
        :type changes: PatchType
        :param original: the original bucket, from which the ID and
            last_modified can be taken
        :type original: dict
        """
        ...
    @retry_timeout
    def get_group(self, *, id, bucket=...) -> Dict: ...
    @retry_timeout
    def delete_group(
        self, *, id, bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    @retry_timeout
    def delete_groups(self, *, bucket=..., safe=..., if_match=...) -> Dict: ...
    def get_collections(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    @retry_timeout
    def create_collection(
        self,
        *,
        id=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    @retry_timeout
    def update_collection(
        self, *, id=..., bucket=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    @retry_timeout
    def patch_collection(
        self,
        *,
        id=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict:
        """Issue a PATCH request on a collection.

        :param changes: the patch to apply
        :type changes: PatchType
        :param original: the original collection, from which the ID and
            last_modified can be taken
        :type original: dict
        """
        ...
    @retry_timeout
    def get_collection(self, *, id=..., bucket=..., **kwargs) -> Dict: ...
    @retry_timeout
    def delete_collection(
        self, *, id=..., bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    @retry_timeout
    def delete_collections(self, *, bucket=..., safe=..., if_match=...) -> Dict: ...
    def get_records_timestamp(self, *, collection=..., bucket=...) -> str: ...
    @retry_timeout
    def get_records(self, *, collection=..., bucket=..., **kwargs) -> List[Dict]:
        """Returns all the records"""
        ...
    def get_paginated_records(
        self, *, collection=..., bucket=..., **kwargs
    ) -> List[Dict]: ...
    @retry_timeout
    def get_record(self, *, id, collection=..., bucket=..., **kwargs) -> Dict: ...
    @retry_timeout
    def create_record(
        self,
        *,
        id=...,
        bucket=...,
        collection=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    @retry_timeout
    def update_record(
        self,
        *,
        id=...,
        collection=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    @retry_timeout
    def patch_record(
        self,
        *,
        id=...,
        collection=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict:
        """Issue a PATCH request on a record.

        :param changes: the patch to apply
        :type changes: PatchType
        :param original: the original record, from which the ID and
            last_modified can be taken
        :type original: dict
        """
        ...
    @retry_timeout
    def delete_record(
        self, *, id, collection=..., bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    @retry_timeout
    def delete_records(
        self, *, collection=..., bucket=..., safe=..., if_match=...
    ) -> Dict: ...
    @retry_timeout
    def get_history(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    @retry_timeout
    def purge_history(self, *, bucket=..., safe=..., if_match=...) -> List[Dict]: ...
    def __repr__(self) -> str: ...

class AsyncClient:
    def __init__(
        self,
        *,
        server_url=...,
        session=...,
        auth=...,
        bucket=...,
        collection=...,
        retry=...,
        retry_after=...,
        timeout=...,
        ignore_batch_4xx=...,
        headers=...
    ) -> None: ...
    def clone(self, **kwargs): ...
    async def server_info(self) -> Dict: ...
    async def get_bucket(self, *, id=..., **kwargs) -> Dict: ...
    async def get_buckets(self, **kwargs) -> List[Dict]: ...
    async def create_bucket(
        self, *, id=..., data=..., permissions=..., safe=..., if_not_exists=...
    ) -> Dict: ...
    async def update_bucket(
        self, *, id=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    async def patch_bucket(
        self,
        *,
        id=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    async def delete_bucket(
        self, *, id=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    async def delete_buckets(self, *, safe=..., if_match=...) -> Dict: ...
    async def get_group(self, *, id, bucket=...) -> Dict: ...
    async def get_groups(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    async def create_group(
        self,
        *,
        id=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    async def update_group(
        self, *, id=..., bucket=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    async def patch_group(
        self,
        *,
        id=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    async def delete_group(
        self, *, id, bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    async def delete_groups(self, *, bucket=..., safe=..., if_match=...) -> Dict: ...
    async def get_collection(self, *, id=..., bucket=..., **kwargs) -> Dict: ...
    async def get_collections(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    async def create_collection(
        self,
        *,
        id=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    async def update_collection(
        self, *, id=..., bucket=..., data=..., permissions=..., safe=..., if_match=...
    ) -> Dict: ...
    async def patch_collection(
        self,
        *,
        id=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    async def delete_collection(
        self, *, id=..., bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    async def delete_collections(self, *, bucket=..., safe=..., if_match=...) -> Dict: ...
    async def get_record(self, *, id, collection=..., bucket=..., **kwargs) -> Dict: ...
    async def get_records(
        self, *, collection=..., bucket=..., **kwargs
    ) -> List[Dict]: ...
    async def get_paginated_records(
        self, *, collection=..., bucket=..., **kwargs
    ) -> List[Dict]: ...
    async def get_records_timestamp(self, *, collection=..., bucket=...) -> str: ...
    async def create_record(
        self,
        *,
        id=...,
        bucket=...,
        collection=...,
        data=...,
        permissions=...,
        safe=...,
        if_not_exists=...
    ) -> Dict: ...
    async def update_record(
        self,
        *,
        id=...,
        collection=...,
        bucket=...,
        data=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    async def patch_record(
        self,
        *,
        id=...,
        collection=...,
        bucket=...,
        changes=...,
        data=...,
        original=...,
        permissions=...,
        safe=...,
        if_match=...
    ) -> Dict: ...
    async def delete_record(
        self, *, id, collection=..., bucket=..., safe=..., if_match=..., if_exists=...
    ) -> Dict: ...
    async def delete_records(
        self, *, collection=..., bucket=..., safe=..., if_match=...
    ) -> Dict: ...
    async def get_history(self, *, bucket=..., **kwargs) -> List[Dict]: ...
    async def purge_history(
        self, *, bucket=..., safe=..., if_match=...
    ) -> List[Dict]: ...
    async def get_endpoint(
        self, name, *, bucket=..., group=..., collection=..., id=...
    ) -> str: ...
    def __repr__(self) -> str: ...
