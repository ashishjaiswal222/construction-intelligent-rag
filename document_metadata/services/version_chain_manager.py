from document_metadata.repositories.metadata_repository import MetadataRepository

class VersionChainManager:
    """
    When a new revision of a document arrives, mark the
    previous revision as not current.

    Example:
      Drawing S-023 Rev A exists with is_current=True.
      Drawing S-023 Rev B arrives.
      VersionChainManager marks Rev A is_current=False,
      superseded_by_id=Rev B's document_id.
      Marks Rev B is_current=True.

    This is the mechanism that prevents the version blindness
    failure mode described in the handbook Chapter 1.
    """

    def __init__(self, repository: MetadataRepository):
        self.repo = repository

    def update_chain(
        self,
        document_id: str,
        drawing_number: str,
        project_id: str,
        new_revision: str,
    ) -> bool:
        """
        Returns True if a previous revision was found and updated.
        Returns False if this is the first revision.
        Must be wrapped in transaction.atomic() by caller.
        """
        if not drawing_number or not project_id:
            return False

        previous = self.repo.find_current_revision(
            drawing_number=drawing_number,
            project_id=project_id,
            exclude_document_id=document_id,
        )

        if previous is None:
            return False

        # Mark previous as superseded
        self.repo.mark_superseded(
            document_id=previous['document_id'],
            superseded_by_id=document_id,
        )
        return True

    def set_is_current(
        self,
        document_id: str,
        is_current: bool,
    ) -> None:
        self.repo.set_is_current(document_id, is_current)
