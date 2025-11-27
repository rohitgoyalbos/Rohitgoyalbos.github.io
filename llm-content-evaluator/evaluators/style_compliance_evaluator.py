"""
Style Compliance Evaluator for LLM Content Quality Evaluator.
Checks adherence to formatting and structural style guidelines.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class FormattingScore:
    """Formatting compliance result."""
    score: float
    capitalization_issues: List[str] = field(default_factory=list)
    punctuation_issues: List[str] = field(default_factory=list)
    number_issues: List[str] = field(default_factory=list)
    unit_issues: List[str] = field(default_factory=list)


@dataclass
class StructureScore:
    """Structural compliance result."""
    score: float
    paragraph_issues: List[str] = field(default_factory=list)
    list_issues: List[str] = field(default_factory=list)
    heading_issues: List[str] = field(default_factory=list)


@dataclass
class ContentRulesScore:
    """Content rules compliance result."""
    score: float
    missing_sections: List[str] = field(default_factory=list)
    prohibited_content: List[str] = field(default_factory=list)
    disclaimer_issues: List[str] = field(default_factory=list)


@dataclass
class StyleComplianceScore:
    """Style compliance evaluation result."""
    score: float
    formatting_score: float
    structure_score: float
    content_rules_score: float
    formatting_issues: List[str] = field(default_factory=list)
    structure_issues: List[str] = field(default_factory=list)
    content_issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


class StyleComplianceEvaluator:
    """
    Evaluates compliance with formatting and structural style rules.

    Categories:
    1. Formatting rules (capitalization, punctuation, numbers)
    2. Structural rules (headings, paragraphs, lists)
    3. Content rules (required sections, prohibited content)
    """

    # Default style rules
    DEFAULT_RULES = {
        "sentence_length_max": 25,
        "paragraph_sentences_max": 4,
        "bullets_min": 3,
        "bullets_max": 7,
        "capitalization": "sentence_case",  # sentence_case, title_case, lowercase
        "number_rule": "spell_small",  # spell_small = spell 1-9, digits for 10+
        "unit_format": "space",  # space = "5 GB", no_space = "5GB"
    }

    # Common formatting patterns
    TITLE_CASE_EXCEPTIONS = {
        'a', 'an', 'the', 'and', 'but', 'or', 'nor', 'for', 'yet', 'so',
        'in', 'on', 'at', 'to', 'by', 'up', 'as', 'of', 'off'
    }

    NUMBER_WORDS = {
        '1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five',
        '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine'
    }

    UNIT_PATTERNS = [
        (r'(\d+)\s*(GB|TB|MB|KB)', 'storage'),
        (r'(\d+)\s*(mm|cm|m|km)', 'length'),
        (r'(\d+)\s*(g|kg|oz|lb)', 'weight'),
        (r'(\d+)\s*(mAh|Wh)', 'battery'),
        (r'(\d+)\s*(Hz|MHz|GHz)', 'frequency'),
    ]

    def __init__(self, style_guide: Optional[Dict] = None):
        """Initialize the style compliance evaluator."""
        self.rules = style_guide or self.DEFAULT_RULES

    def check_formatting(self, content: str) -> FormattingScore:
        """
        Check formatting compliance.

        Rules to check:
        - Title case vs sentence case
        - Punctuation consistency
        - Number formatting (1-9 spelled out vs digits)
        - Unit formatting (5GB vs 5 GB)
        """
        issues_caps = []
        issues_punct = []
        issues_numbers = []
        issues_units = []

        # Check capitalization
        cap_rule = self.rules.get("capitalization", "sentence_case")
        sentences = re.split(r'[.!?]+', content)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            words = sentence.split()
            if not words:
                continue

            # Check first word capitalization
            first_word = words[0]
            if first_word and first_word[0].islower():
                if not first_word.startswith(('http', 'www', '@')):
                    issues_caps.append(f"Sentence should start with capital: '{sentence[:40]}...'")

            # Check for ALL CAPS (except acronyms)
            for word in words:
                if len(word) > 3 and word.isupper():
                    if word not in {'USB', 'LED', 'LCD', 'HDMI', 'GPS', 'WIFI', 'OLED', 'RAM', 'SSD', 'CPU', 'GPU'}:
                        issues_caps.append(f"Avoid all caps: '{word}'")

        # Check punctuation consistency
        # Multiple exclamation/question marks
        if re.search(r'[!?]{2,}', content):
            issues_punct.append("Avoid multiple exclamation or question marks")

        # Missing space after punctuation
        if re.search(r'[.!?,][A-Za-z]', content):
            issues_punct.append("Missing space after punctuation")

        # Double spaces
        if '  ' in content:
            issues_punct.append("Remove double spaces")

        # Check number formatting
        number_rule = self.rules.get("number_rule", "spell_small")
        if number_rule == "spell_small":
            # Find standalone digits 1-9
            for match in re.finditer(r'\b([1-9])\b(?!\d)', content):
                digit = match.group(1)
                # Skip if it's part of a measurement or version
                context = content[max(0, match.start()-5):min(len(content), match.end()+10)]
                if not re.search(r'(\d+\.|v\d|[.-]\d|\d[x×]|\d+%|#\d)', context, re.IGNORECASE):
                    if not re.search(r'\d+\s*(?:GB|TB|MB|mm|cm|g|kg|mAh)', context, re.IGNORECASE):
                        issues_numbers.append(f"Spell out small numbers: '{digit}' → '{self.NUMBER_WORDS.get(digit, digit)}'")

        # Check unit formatting
        unit_format = self.rules.get("unit_format", "space")
        for pattern, unit_type in self.UNIT_PATTERNS:
            for match in re.finditer(pattern, content):
                full_match = match.group(0)
                has_space = ' ' in full_match or re.match(r'\d+\s+\w', full_match)

                if unit_format == "space" and not has_space:
                    issues_units.append(f"Add space between number and unit: '{full_match}'")
                elif unit_format == "no_space" and has_space:
                    issues_units.append(f"Remove space between number and unit: '{full_match}'")

        # Calculate score
        total_issues = len(issues_caps) + len(issues_punct) + len(issues_numbers) + len(issues_units)
        score = max(0, 100 - (total_issues * 5))

        return FormattingScore(
            score=score,
            capitalization_issues=issues_caps[:5],
            punctuation_issues=issues_punct[:5],
            number_issues=issues_numbers[:5],
            unit_issues=issues_units[:5]
        )

    def check_structure(self, content: str) -> StructureScore:
        """
        Check structural compliance.

        Rules to check:
        - Paragraph length limits
        - List formatting (parallel structure)
        - Heading hierarchy
        """
        issues_para = []
        issues_list = []
        issues_heading = []

        max_para_sentences = self.rules.get("paragraph_sentences_max", 4)
        min_bullets = self.rules.get("bullets_min", 3)
        max_bullets = self.rules.get("bullets_max", 7)

        # Check paragraph length
        paragraphs = content.split('\n\n')
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue

            # Count sentences in paragraph
            sentences = re.split(r'[.!?]+', para)
            sentences = [s for s in sentences if s.strip()]

            if len(sentences) > max_para_sentences:
                issues_para.append(
                    f"Paragraph {i+1} has {len(sentences)} sentences (max {max_para_sentences})"
                )

        # Check bullet list formatting
        bullet_groups = re.findall(r'((?:(?:•|·|\*|-)\s+[^\n]+\n?)+)', content)
        for group in bullet_groups:
            bullets = re.findall(r'(?:•|·|\*|-)\s+([^\n]+)', group)

            # Check count
            if len(bullets) < min_bullets:
                issues_list.append(f"List has only {len(bullets)} items (min {min_bullets})")
            elif len(bullets) > max_bullets:
                issues_list.append(f"List has {len(bullets)} items (max {max_bullets})")

            # Check parallel structure (simplified - check first word consistency)
            if bullets:
                first_words = [b.split()[0] if b.split() else '' for b in bullets]
                # Check if they're consistently verbs or nouns
                verb_endings = ('s', 'ed', 'ing')
                verb_count = sum(1 for w in first_words if w.lower().endswith(verb_endings))

                if 0 < verb_count < len(first_words):
                    issues_list.append("Bullet points lack parallel structure")

        # Check heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        if headings:
            levels = [len(h[0]) for h in headings]
            # Check for skipped levels
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    issues_heading.append(f"Heading hierarchy skips level: H{levels[i-1]} to H{levels[i]}")

        # Calculate score
        total_issues = len(issues_para) + len(issues_list) + len(issues_heading)
        score = max(0, 100 - (total_issues * 10))

        return StructureScore(
            score=score,
            paragraph_issues=issues_para[:5],
            list_issues=issues_list[:5],
            heading_issues=issues_heading[:5]
        )

    def check_content_rules(
        self,
        content: str,
        required_sections: Optional[List[str]] = None,
        prohibited_patterns: Optional[List[str]] = None
    ) -> ContentRulesScore:
        """
        Check content-level rules.

        Rules to check:
        - Required sections present
        - Prohibited phrases absent
        - Disclaimer requirements
        """
        issues_missing = []
        issues_prohibited = []
        issues_disclaimer = []

        content_lower = content.lower()

        # Check required sections
        if required_sections:
            for section in required_sections:
                if section.lower() not in content_lower:
                    issues_missing.append(f"Missing required section: {section}")

        # Check prohibited patterns
        default_prohibited = [
            r'\b(?:guarantee[sd]?\s+(?:results|success|outcome))',
            r'\b(?:100%\s+(?:safe|effective|guaranteed))',
            r'\b(?:no\s+risk)',
            r'\b(?:miracle|magic|instant\s+(?:results|cure))',
        ]

        patterns_to_check = prohibited_patterns or default_prohibited
        for pattern in patterns_to_check:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                issues_prohibited.append(f"Prohibited content found: '{matches[0]}'")

        # Check for common disclaimer requirements
        # (This is a simplified check - real implementation would be more comprehensive)
        if re.search(r'\b(?:health|medical|treatment|cure)\b', content, re.IGNORECASE):
            if not re.search(r'\b(?:consult|doctor|physician|healthcare|professional)\b', content, re.IGNORECASE):
                issues_disclaimer.append("Health-related content may need medical disclaimer")

        if re.search(r'\b(?:invest|financial|money|profit|return)\b', content, re.IGNORECASE):
            if not re.search(r'\b(?:risk|past\s+performance|guarantee)\b', content, re.IGNORECASE):
                issues_disclaimer.append("Financial content may need risk disclaimer")

        # Calculate score
        total_issues = len(issues_missing) + len(issues_prohibited) + len(issues_disclaimer)
        score = max(0, 100 - (total_issues * 15))

        return ContentRulesScore(
            score=score,
            missing_sections=issues_missing,
            prohibited_content=issues_prohibited,
            disclaimer_issues=issues_disclaimer
        )

    def evaluate(
        self,
        content: str,
        required_sections: Optional[List[str]] = None,
        prohibited_patterns: Optional[List[str]] = None
    ) -> StyleComplianceScore:
        """
        Main evaluation method.

        Returns composite style compliance score.
        """
        # Handle content dict
        if isinstance(content, dict):
            text_parts = []
            for field in ['description', 'marketing_copy', 'meta_description']:
                if field in content and content[field]:
                    text_parts.append(str(content[field]))
            if 'feature_bullets' in content and content['feature_bullets']:
                if isinstance(content['feature_bullets'], list):
                    # Format as bullet list for structure checking
                    text_parts.append('\n'.join([f"• {b}" for b in content['feature_bullets']]))
            content = "\n\n".join(text_parts)

        # Run component evaluations
        formatting_result = self.check_formatting(content)
        structure_result = self.check_structure(content)
        content_rules_result = self.check_content_rules(
            content, required_sections, prohibited_patterns
        )

        # Calculate composite score
        composite = (
            formatting_result.score * 0.35 +
            structure_result.score * 0.35 +
            content_rules_result.score * 0.30
        )

        # Collect all issues
        all_formatting = (
            formatting_result.capitalization_issues +
            formatting_result.punctuation_issues +
            formatting_result.number_issues +
            formatting_result.unit_issues
        )

        all_structure = (
            structure_result.paragraph_issues +
            structure_result.list_issues +
            structure_result.heading_issues
        )

        all_content = (
            content_rules_result.missing_sections +
            content_rules_result.prohibited_content +
            content_rules_result.disclaimer_issues
        )

        return StyleComplianceScore(
            score=round(composite, 2),
            formatting_score=round(formatting_result.score, 2),
            structure_score=round(structure_result.score, 2),
            content_rules_score=round(content_rules_result.score, 2),
            formatting_issues=all_formatting[:10],
            structure_issues=all_structure[:10],
            content_issues=all_content[:10],
            details={
                "capitalization_issues": formatting_result.capitalization_issues,
                "punctuation_issues": formatting_result.punctuation_issues,
                "number_issues": formatting_result.number_issues,
                "unit_issues": formatting_result.unit_issues,
                "paragraph_issues": structure_result.paragraph_issues,
                "list_issues": structure_result.list_issues,
                "heading_issues": structure_result.heading_issues,
                "missing_sections": content_rules_result.missing_sections,
                "prohibited_content": content_rules_result.prohibited_content,
                "disclaimer_issues": content_rules_result.disclaimer_issues
            }
        )

    def update_rules(self, rules: Dict) -> None:
        """Update style rules."""
        self.rules.update(rules)
