"""Render the canonical structured article body for DB drafts and RSS."""

from html import escape


def _paragraphs(values: list[str]) -> str:
    return "".join(f"<p>{escape(value)}</p>" for value in values)


def render_article_content_html(
    article: dict[str, object],
    *,
    eligible_article_slugs: set[str] | None = None,
) -> str:
    sections: list[str] = [
        "<header>",
        f"<p>{escape(str(article['summary']))}</p>",
        "</header>",
        "<section>",
        f"<h2>{escape(str(article['direct_answer_title']))}</h2>",
        _paragraphs(list(article["direct_answer_paragraphs"])),
        "</section>",
        "<section><h2>이 글이 필요한 사람</h2><ul>",
    ]
    sections.extend(f"<li>{escape(str(item))}</li>" for item in article["audience_items"])
    sections.append("</ul></section>")

    sections.append("<section><h2>다음에 읽을 글</h2><ul>")
    for related in article["related_articles"]:
        related_path = str(related["path"])
        related_slug = related_path.removeprefix("/blog/") if related_path.startswith("/blog/") else ""
        if eligible_article_slugs is not None and related_slug not in eligible_article_slugs:
            continue
        sections.append(
            f'<li><a href="{escape(related_path, quote=True)}">'
            f"{escape(str(related['title']))}</a> — {escape(str(related['summary']))}</li>"
        )
    sections.append("</ul></section>")

    sections.append(
        "<section><h2>편집·검수 정보</h2>"
        f"<p>작성: {escape(str(article['author']))}. 검수 책임: {escape(str(article['review_owner']))}. "
        f"기준일 {escape(str(article['effective_date']))}, 검수일 {escape(str(article['reviewed_at']))}, "
        f"재검수 기한 {escape(str(article['expires_at']))}.</p>"
        f"<p>주제 태그: {escape(', '.join(str(tag) for tag in article['tags']))}. "
        "제도와 공식 안내는 변경될 수 있으므로 재검수 기한이 지났다면 연결된 기관의 최신 문서를 우선합니다.</p>"
        f"<p>편집 요약: {escape(str(article['meta_description']))}</p>"
        "</section>"
    )

    for content_section in article.get("content_sections", []):
        sections.extend(
            [
                "<section>",
                f"<h2>{escape(str(content_section['heading']))}</h2>",
                _paragraphs(list(content_section["paragraphs"])),
                "</section>",
            ]
        )

    sections.append("<section><h2>상황별 사례</h2>")
    for card in article["example_cards"]:
        sections.extend(
            [
                f"<h3>{escape(str(card['title']))}</h3>",
                f"<p>{escape(str(card['description']))}</p>",
            ]
        )
    sections.append("</section>")

    sections.append("<section><h2>기준 비교</h2><table><tbody>")
    for row in article["comparison_rows"]:
        sections.append(
            "<tr>"
            f"<th>{escape(str(row['label']))}</th>"
            f"<td>{escape(str(row['standard']))}</td>"
            f"<td>{escape(str(row['exception']))}</td>"
            "</tr>"
        )
    sections.append("</tbody></table></section>")

    sections.append("<section><h2>자주 묻는 질문</h2>")
    for faq in article["faq_items"]:
        sections.extend(
            [
                f"<h3>{escape(str(faq['question']))}</h3>",
                f"<p>{escape(str(faq['answer']))}</p>",
            ]
        )
    sections.append("</section>")

    sections.append("<section><h2>AgeCalc에서 확인하기</h2><ul>")
    for tool in article["related_tools"]:
        sections.append(
            f'<li><a href="{escape(str(tool["path"]), quote=True)}">'
            f"{escape(str(tool['label']))}</a> — {escape(str(tool['summary']))}</li>"
        )
    sections.append("</ul></section>")

    if article.get("disclaimer"):
        sections.append(f"<p><strong>안내:</strong> {escape(str(article['disclaimer']))}</p>")

    sections.append("<section><h2>공식 출처</h2><ul>")
    for source in article["source_urls"]:
        sections.append(
            f'<li><a href="{escape(str(source["url"]), quote=True)}" rel="noopener noreferrer">'
            f"{escape(str(source['organization']))} — {escape(str(source['title']))}</a>"
            f" (확인일 {escape(str(source['checked_at']))})</li>"
        )
    sections.append("</ul></section>")
    return "".join(sections)
