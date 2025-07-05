from dataclasses import dataclass


@dataclass
class AlignedToken:
    id: int
    text: str
    start: float
    duration: float
    end: float = 0.0  # temporary

    def __post_init__(self) -> None:
        self.end = self.start + self.duration


@dataclass
class AlignedSentence:
    text: str
    tokens: list[AlignedToken]
    start: float = 0.0  # temporary
    end: float = 0.0  # temporary
    duration: float = 0.0  # temporary

    def __post_init__(self) -> None:
        self.tokens = list(sorted(self.tokens, key=lambda x: x.start))
        self.start = self.tokens[0].start
        self.end = self.tokens[-1].end
        self.duration = self.end - self.start


@dataclass
class AlignedResult:
    text: str
    sentences: list[AlignedSentence]

    def __post_init__(self) -> None:
        self.text = self.text.strip()

    @property
    def tokens(self) -> list[AlignedToken]:
        return [token for sentence in self.sentences for token in sentence.tokens]


def tokens_to_sentences(tokens: list[AlignedToken]) -> list[AlignedSentence]:
    sentences = []
    current_tokens = []

    for idx, token in enumerate(tokens):
        current_tokens.append(token)

        # hacky, will fix
        if (
            "!" in token.text
            or "?" in token.text
            or "。" in token.text
            or "？" in token.text
            or "！" in token.text
            or (
                "." in token.text
                and (idx == len(tokens) - 1 or " " in tokens[idx + 1].text)
            )
        ):  # type: ignore
            sentence_text = "".join(t.text for t in current_tokens)
            sentence = AlignedSentence(text=sentence_text, tokens=current_tokens)
            sentences.append(sentence)

            current_tokens = []

    if current_tokens:
        sentence_text = "".join(t.text for t in current_tokens)
        sentence = AlignedSentence(text=sentence_text, tokens=current_tokens)
        sentences.append(sentence)

    return sentences


def sentences_to_result(sentences: list[AlignedSentence]) -> AlignedResult:
    return AlignedResult("".join(sentence.text for sentence in sentences), sentences)

# TODO: find out why there is numeric instability at boundary and reverse this
def merge_longest_contiguous(
    a: list[AlignedToken],
    b: list[AlignedToken],
    *,
    overlap_duration: float,
):
    if not a or not b:
        return b if not a else a

    a_end_time = a[-1].end
    b_start_time = b[0].start

    if a_end_time <= b_start_time:
        return a + b

    # simple midpoint merge
    overlap_start = b_start_time
    overlap_end = a_end_time
    overlap_midpoint = (overlap_start + overlap_end) / 2
    
    # tiny earlier cutoff to get more chunk A tokens
    cutoff_time = overlap_midpoint - 0.1
    
    # ..A |<-mid point B..
    result = []
    for token in a:
        if token.end <= cutoff_time:
            result.append(token)
    
    for token in b:
        if token.start > cutoff_time:
            result.append(token)
    
    return result


def merge_longest_common_subsequence(
    a: list[AlignedToken],
    b: list[AlignedToken],
    *,
    overlap_duration: float,
):
    # forgive me for i have sinned
    return merge_longest_contiguous(a, b, overlap_duration=overlap_duration)
