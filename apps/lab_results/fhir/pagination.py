"""FHIR Bundle pagination for /fhir/DiagnosticReport.

We extend DRF's PageNumberPagination so list views get the same role-filter
behaviour as before, then translate the page state into Bundle.link entries
(self/first/next/previous/last) that callers follow opaquely.
"""

from __future__ import annotations

from urllib.parse import urlencode, urlparse, urlunparse

from fhir.resources.bundle import BundleLink
from rest_framework.pagination import PageNumberPagination


class FHIRBundlePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "_count"
    max_page_size = 100

    def _replace_page(self, request, page_number: int | None) -> str:
        """Build a URL identical to the current request but with page=N."""
        url = request.build_absolute_uri()
        parsed = urlparse(url)
        # Drop the existing `page` param and overlay ours.
        query_pairs = [
            (k, v)
            for k, v in (
                pair.split("=", 1) if "=" in pair else (pair, "")
                for pair in parsed.query.split("&")
                if pair
            )
            if k != "page"
        ]
        if page_number is not None:
            query_pairs.append(("page", str(page_number)))
        new_query = urlencode(query_pairs)
        return urlunparse(parsed._replace(query=new_query))

    def get_bundle_links(self, request) -> list[BundleLink]:
        """Translate paginator state into Bundle.link entries."""
        if not hasattr(self, "page") or self.page is None:
            # No pagination context — at minimum a self link.
            return [BundleLink(relation="self", url=request.build_absolute_uri())]

        last_page = self.page.paginator.num_pages

        links: list[BundleLink] = [
            BundleLink(relation="self", url=request.build_absolute_uri()),
            BundleLink(relation="first", url=self._replace_page(request, 1)),
            BundleLink(relation="last", url=self._replace_page(request, last_page)),
        ]
        if self.page.has_previous():
            links.append(
                BundleLink(
                    relation="previous",
                    url=self._replace_page(request, self.page.previous_page_number()),
                )
            )
        if self.page.has_next():
            links.append(
                BundleLink(
                    relation="next",
                    url=self._replace_page(request, self.page.next_page_number()),
                )
            )
        return links
