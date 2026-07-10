"""Catalog service skeleton for products, materials, samples, and topics."""

from app.repositories.interaction_type_repository import InteractionTypeRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.sample_repository import SampleRepository
from app.repositories.topic_repository import TopicRepository


class CatalogService:
    """Application service for reference catalog entities."""

    def __init__(
        self,
        interaction_type_repository: InteractionTypeRepository,
        product_repository: ProductRepository,
        material_repository: MaterialRepository,
        sample_repository: SampleRepository,
        topic_repository: TopicRepository,
    ) -> None:
        self._interaction_type_repository = interaction_type_repository
        self._product_repository = product_repository
        self._material_repository = material_repository
        self._sample_repository = sample_repository
        self._topic_repository = topic_repository
