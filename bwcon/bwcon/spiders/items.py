import dataclasses


@dataclasses.dataclass
class BwConArticle:
    title: str
    pub_date: str
    description: str
    content: str

    def __repr__(self):
        return (
            f'<BwConArticle '
            f'title: "{self.title[:24]}…" '
            f'pub_date: "{self.pub_date}" '
            f'description: "{self.description[:24]}…" '
            f'content: "{self.content[:24]}…"'
            f'>'
        )
