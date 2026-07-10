"""Healthcare professional search and history endpoints."""

import time
from uuid import UUID

from fastapi import APIRouter, Depends, Request

from app.api.response import success_response
from app.core.dependencies import HcpServiceDep
from app.schemas.common import PaginatedResponse
from app.schemas.hcp_api import HcpHistoryResponse, HcpSearchQuery, HcpSearchResultItem
from app.schemas.responses import ApiResponse

router = APIRouter(prefix="/hcp", tags=["HCP"])


@router.get(
    "/search",
    response_model=ApiResponse[PaginatedResponse[HcpSearchResultItem]],
    summary="Search healthcare professionals",
)
async def search_hcps(
    request: Request,
    hcp_service: HcpServiceDep,
    query: HcpSearchQuery = Depends(),
) -> ApiResponse[PaginatedResponse[HcpSearchResultItem]]:
    """Search HCPs by doctor name, hospital, city, and specialization."""
    start_time = time.perf_counter()
    results = await hcp_service.search_hcps(query)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="HCP search completed successfully.",
        data=results,
        execution_time_ms=elapsed_ms,
        extra_meta={
            "page": results.meta.page,
            "page_size": results.meta.page_size,
            "total_items": results.meta.total_items,
        },
    )


@router.get(
    "/{hcp_id}/history",
    response_model=ApiResponse[HcpHistoryResponse],
    summary="Get HCP interaction history",
)
async def get_hcp_history(
    request: Request,
    hcp_id: UUID,
    hcp_service: HcpServiceDep,
) -> ApiResponse[HcpHistoryResponse]:
    """Return previous interactions for a healthcare professional."""
    start_time = time.perf_counter()
    history = await hcp_service.get_hcp_history(hcp_id)
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return success_response(
        request=request,
        message="HCP interaction history retrieved successfully.",
        data=history,
        execution_time_ms=elapsed_ms,
    )
