import random
import re

from genanki import Model, Deck, Note, Package
from markdown import markdown

from database_cn import Problem
from utils import parser as conf


def random_id():
    return random.randrange(1 << 30, 1 << 31)


def markdown_to_html(content: str):
    # replace the math symbol "$x$" to "\[$]x\[/$]" to make it compatible with mathjax
    # content = re.sub(pattern=r"\$(.*?)\$", repl=r"[$]\1[/$]", string=content)
    # def replacement(match):
    #    return '``` '+match.group(1).lower()
    # content = re.sub(r'```(.*) *\[sol.*\]', replacement, content)
    with open("./mathjax.txt", "r") as f:
        mathjax_prefix = "".join(f.readlines()) + "\n"
    extension_configs = {
        "pymdownx.highlight": {
            "auto_title": True,
            "linenums_style": "inline",
            "line_spans": "__codeline",
            "line_anchors": "__codelineno",
            "anchor_linenums": True,
        },
        "mdx_math": {
            "enable_dollar_delimiter": True,  # 是否启用单美元符号（默认只启用双美元）
            "add_preview": True,  # 在公式加载成功前是否启用预览（默认不启用）
        },
    }

    content = re.sub(r"\s*\[sol.*\]", "", content)
    

    def process_gif(content):
        lines = content.split("\n")
        for i in range(len(lines)):
            if lines[i].startswith("<!") and lines[i].endswith(">"):
                lines[i] = '\n'.join(lines[i][1:-1].split(','))
        return '\n'.join(lines)
    content = process_gif(content)
    #print(content)



    # also need to load the mathjax and toc extensions
    #print(
    #    mathjax_prefix
    #    + markdown(
    #        content,
    #        extensions=[
    #            "mdx_math",
    #            "toc",
    #            "pymdownx.superfences",
    #            "tables",
    #            "attr_list",
    #            "pymdownx.highlight",
    #        ],
    #        extension_configs=extension_configs,
    #    )
    #)
    return mathjax_prefix + markdown(
        content,
        extensions=[
            "mdx_math",
            "toc",
            "pymdownx.superfences",
            "tables",
            "attr_list",
            "pymdownx.highlight",
        ],
        extension_configs=extension_configs,
    )


def code_to_html(source, language):
    content = f"```{language}\n{source}\n```"
    return markdown(content, extensions=["fenced_code"])


def get_anki_model():
    with open(conf.get("Anki", "front"), "r") as f:
        front_template = f.read()
    with open(conf.get("Anki", "back"), "r") as f:
        back_template = f.read()
    with open(conf.get("Anki", "css"), "r") as f:
        css = f.read()

    anki_model = Model(
        model_id=1048217874,
        name="LeetCode",
        fields=[
            {"name": "ID"},
            {"name": "Title"},
            {"name": "TitleSlug"},
            {"name": "Difficulty"},
            {"name": "Description"},
            {"name": "Tags"},
            {"name": "TagSlugs"},
            {"name": "Solution"},
            {"name": "Submission"},
        ],
        templates=[{"name": "LeetCode", "qfmt": front_template, "afmt": back_template}],
        css=css,
    )
    return anki_model


def make_note(problem):
    print(f"📓 Producing note for problem: {problem.title}...")
    tags = ";".join([t.name for t in problem.tags])
    tags_slug = ";".join([t.slug for t in problem.tags])

    try:
        solution = problem.solution.get()
    except Exception:
        print("failed")
        solution = None

    codes = []
    for item in problem.submissions:
        source = re.sub(
            r"(\\u[\s\S]{4})",
            lambda x: x.group(1).encode("utf-8").decode("unicode-escape"),
            item.source,
        )
        output = code_to_html(source, item.language)
        codes.append(output)
    submissions = "\n".join(codes)

    note = Note(
        model=get_anki_model(),
        fields=[
            str(problem.display_id),
            problem.title,
            problem.slug,
            problem.level,
            problem.description,
            tags,
            tags_slug,
            markdown_to_html(solution.content) if solution else "",
            submissions,
        ],
        guid=str(problem.display_id),
        sort_field=str(problem.display_id),
        tags=[t.slug for t in problem.tags],
    )
    return note


def render_anki():
    problems = Problem.select().order_by(Problem.display_id)

    anki_deck = Deck(deck_id=random_id(), name="LeetCodeCN-hot100")

    for problem in problems:
        note = make_note(problem)
        anki_deck.add_note(note)

    path = conf.get("Anki_CN", "output")
    Package(anki_deck).write_to_file(path)


if __name__ == "__main__":
    render_anki()
