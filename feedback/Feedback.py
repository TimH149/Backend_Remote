import ollama
from difflib import SequenceMatcher
import spacy

# Laad het Nederlandse taalmodel
nlp = spacy.load("nl_core_news_sm")

def prompt_EULLM(prompt, stream_):
    stream =  ollama.chat(
        model="jobautomation/OpenEuroLLM-Dutch",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0.0,
            "num_gpu": 99,
        },
        keep_alive="30m",
    )
    if stream_:
        result = ""
        for chunk in stream:
            result += chunk["message"]["content"]
            print(chunk["message"]["content"], end="", flush=True)
        print("")
        return result.strip()
    else:
        return stream["message"]["content"].strip()

def get_modified_word(token):
    """
    Find the word that the changed determiner/relative pronoun
    refers to.
    """

    # --------------------------------------------------
    # Determiners
    # deze meisje -> meisje
    # dit huis    -> huis
    # het straat  -> straat
    # --------------------------------------------------
    if token.dep_ == "det":
        head = token.head

        if head.pos_ in {"NOUN", "PROPN", "PRON"}:
            return head

    # --------------------------------------------------
    # Relative pronouns
    # Het boek die ik lees
    #          ^^^
    # --------------------------------------------------
    if (
        token.pos_ == "PRON"
        and "Rel" in token.morph.get("PronType")
    ):
        # The relative pronoun usually belongs to the
        # relative-clause verb.
        head = token.head

        # Search the verb's children for the antecedent.
        for child in head.children:
            if child.dep_ == "relcl":
                return child

        # Walk upward in case the structure is deeper.
        current = head

        for _ in range(5):
            if current.dep_ == "relcl":
                return current.head

            current = current.head

        # Last fallback: nearest noun/pronoun to the left
        # before the relative pronoun.
        for candidate in reversed(list(token.doc[:token.i])):
            if candidate.pos_ in {"NOUN", "PROPN", "PRON"}:
                return candidate

    # --------------------------------------------------
    # Generic fallback
    # --------------------------------------------------
    if token.head.pos_ in {"NOUN", "PROPN", "PRON"}:
        return token.head

    return None

def get_subject(token):
    """
    Find the subject belonging to a verb.
    """

    # First look at children of the verb
    for child in token.children:
        if child.dep_ in {"nsubj", "nsubj:pass"}:
            return child

    # If token itself is part of a verb construction,
    # check its syntactic head.
    if token.head.pos_ == "VERB":
        for child in token.head.children:
            if child.dep_ in {"nsubj", "nsubj:pass"}:
                return child

    return None


def get_auxiliary(token):
    """
    Find a nearby auxiliary verb.

    Examples:
        heb gezocht
        heeft verzonden
        is gegleden
    """

    # Auxiliary attached to the verb
    for child in token.children:
        if child.pos_ == "AUX":
            return child

    # If this token is itself the participle, look at its head
    if token.head.pos_ == "AUX":
        return token.head

    # Look at nearby tokens as fallback
    for candidate in token.doc:
        if candidate.i >= token.i:
            break

        if candidate.pos_ == "AUX":
            # Don't look arbitrarily far away
            if token.i - candidate.i <= 3:
                return candidate

    return None


def extract_changes(original, corrected):
    doc_orig = nlp(original)
    doc_corr = nlp(corrected)

    original_words = [token.text for token in doc_orig]
    corrected_words = [token.text for token in doc_corr]

    matcher = SequenceMatcher(
        None,
        [word.casefold() for word in original_words], 
        [word.casefold() for word in corrected_words]
    )

    changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag == "equal":
            continue

        # Ignore punctuation so it does not change the grammatical category.
        orig_tokens = [
            token for token in doc_orig[i1:i2]
            if token.pos_ not in {"SPACE", "PUNCT"}
        ]
        corr_tokens = [
            token for token in doc_corr[j1:j2]
            if token.pos_ not in {"SPACE", "PUNCT"}
        ]
        original_part = [token.text for token in orig_tokens]
        corrected_part = [token.text for token in corr_tokens]

        # -----------------------------------------------------
        # 1. Grammatical information
        # -----------------------------------------------------

        orig_ws = ", ".join(
            token.pos_ for token in orig_tokens
        ) or "N/A"

        corr_ws = ", ".join(
            token.pos_ for token in corr_tokens
        ) or "N/A"

        orig_vm_list = [
            token.morph.to_dict()
            for token in orig_tokens
        ]

        corr_vm_list = [
            token.morph.to_dict()
            for token in corr_tokens
        ]

        orig_vm = (
            orig_vm_list
            if len(orig_vm_list) > 1
            else (
                orig_vm_list[0]
                if orig_vm_list
                else {}
            )
        )

        corr_vm = (
            corr_vm_list
            if len(corr_vm_list) > 1
            else (
                corr_vm_list[0]
                if corr_vm_list
                else {}
            )
        )

        # -----------------------------------------------------
        # 2. Dependency-based context
        # -----------------------------------------------------

        modified_word = None
        subject = None
        verb = None
        auxiliary = None
        lemma = None

        # Prefer the corrected sentence for grammatical context
        context_tokens = corr_tokens if corr_tokens else orig_tokens

        for token in context_tokens:

            # -------------------------------------------------
            # Noun modified by de/het/deze/dit/die/dat
            # -------------------------------------------------

            word = get_modified_word(token)

            if word is not None:
                modified_word = word.text

            # -------------------------------------------------
            # Verb
            # -------------------------------------------------

            if token.pos_ in {"VERB", "AUX"}:

                if token.pos_ == "VERB":
                    verb = token.text
                    lemma = token.lemma_

                found_subject = get_subject(token)

                if found_subject is not None:
                    subject = found_subject.text

                found_auxiliary = get_auxiliary(token)

                if found_auxiliary is not None:
                    auxiliary = found_auxiliary.text

        # -----------------------------------------------------
        # 3. If the changed word itself is a verb,
        #    inspect it directly
        # -----------------------------------------------------


        for token in orig_tokens:

            if token.pos_ == "VERB":

                if verb is None:
                    verb = token.text

                if lemma is None:
                    lemma = token.lemma_

                found_subject = get_subject(token)
                if found_subject is not None:
                    subject = found_subject.text

                found_auxiliary = get_auxiliary(token)
                if found_auxiliary is not None:
                    auxiliary = found_auxiliary.text


        # Then inspect corrected tokens for the corrected form.

        for token in corr_tokens:

            if token.pos_ == "VERB":

                if verb is None:
                    verb = token.text

                if lemma is None:
                    lemma = token.lemma_

                found_subject = get_subject(token)
                if found_subject is not None:
                    subject = found_subject.text

                found_auxiliary = get_auxiliary(token)
                if found_auxiliary is not None:
                    auxiliary = found_auxiliary.text
        # -----------------------------------------------------
        # 4. Context sentence with ___
        # -----------------------------------------------------

        context_words = original_words.copy()

        if tag in ("replace", "delete"):
            context_words[i1:i2] = ["___"]

        elif tag == "insert":
            context_words.insert(i1, "___")

        context_sentence = " ".join(context_words)

        # -----------------------------------------------------
        # 5. Store change
        # -----------------------------------------------------

        changes.append(
            {
                "fout": " ".join(original_part),

                "orig_woordsoort": orig_ws,
                "orig_vorm": orig_vm,

                "correctie": " ".join(corrected_part),

                "woordsoort": corr_ws,
                "vorm": corr_vm,

                "zin": context_sentence,

                # Dependency-based context
                "modified_word": modified_word,
                "modified_noun": modified_word,  # backwards compatibility
                "subject": subject,
                "verb": verb,
                "auxiliary": auxiliary,
                "lemma": lemma,

                # Keep the old field temporarily so
                # existing code doesn't immediately break
                "volgend_zn": modified_word,   

                # Useful for later classification
                "operation": tag
            }
        )

    return changes

    

def get_feedback_prompt(changes):
    return f"""Geef één korte hint waarmee een kind van 10 de zin zelf kan verbeteren en inziet wat hij fout doet.

    fout: \"{changes[0]['fout']}\"
    correctie: \"{changes[0]['correctie']}\"
    zin: \"{changes[0]['zin']}\"

    Graag in 1 zin. Geef alleen de hint in niet corrigerende, eenvoudige manier."""

def get_feedback_prompt(changes):
    return f"""Geef één duidelijk korte hint waarmee een kind van 8 inziet wat hij fout doet.

    fout: \"{changes[0]['fout']}\"
 
    zin: \"{changes[0]['zin']}\"
  """

def get_correction_prompt(zin):
    return f"""Corrigeer alleen grammaticale fouten. Verander verder niets. Geef alleen de zin: {zin}"""    




def genereer_feedback(change, feedback_prompt):
    """
    Generate personalized Dutch feedback based on the output
    of extract_changes().

    Input:
        change: one dictionary returned by extract_changes()

    Output:
        str: personalized feedback/question
    """

    fout = change.get("fout", "").strip()
    fout_lower = fout.lower()
    correctie = change.get("correctie", "").strip()
    correctie_lower = correctie.lower()

    orig_pos = change.get("orig_woordsoort")
    corr_pos = change.get("woordsoort")

    orig_vorm = change.get("orig_vorm", {})
    corr_vorm = change.get("vorm", {})

    zin = change.get("zin", "")

    modified_word = change.get("modified_word")
    subject = change.get("subject")
    verb = change.get("verb")
    auxiliary = change.get("auxiliary")
    lemma = change.get("lemma")

    # Store the numbered mistake category selected below so callers can
    # persist or analyze the child's mistake alongside the feedback.
    change["mistake_type"] = None

    # =========================================================
    # 1. VERB AGREEMENT
    # =========================================================

    # Example:
    # De mensen loop ...
    # -> De mensen lopen ...

    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Fin"
        and subject is not None
    ):
        change["mistake_type"] = 1
        number = corr_vorm.get("Number")

        if number == "Plur":
            return (
                f"Je zegt '{subject} {fout}'. "
                f"Wie doet iets: één persoon of meerdere? "
                f"Welke vorm van '{lemma}' hoort daarbij?"
            )

        if number == "Sing":
            return (
                f"Je zegt '{subject} {fout}'. "
                f"Wie doet iets: één persoon of meerdere? "
                f"Welke vorm van '{lemma}' hoort daarbij?"
            )

    # =========================================================
    # 2. PAST PARTICIPLE AFTER AUXILIARY
    # =========================================================

    # Examples:
    # Ik heb ... gezoekt -> gezocht
    # Zij heeft ... verzendt -> verzonden
    # Hij is ... geglijdt -> gegleden

    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Part"
        and auxiliary is not None
        and lemma is not None
    ):
        change["mistake_type"] = 2
        return (
            f"Je zegt '{auxiliary} ... {fout}'. "
            f"Welke vorm van '{lemma}' hoort na '{auxiliary}'?"
        )

    # =========================================================
    # 3. DE / HET
    # =========================================================

    if fout_lower in {"de", "het"} and modified_word is not None:

        change["mistake_type"] = 3

        return (
            f"Je zegt '{fout} {modified_word}'. "
            f"Is '{modified_word}' een de-woord of een het-woord?"
        )

    # =========================================================
    # 4. DEZE / DIT
    # =========================================================

    if fout_lower in {"deze", "dit"} and modified_word is not None:

        change["mistake_type"] = 4

        return (
            f"Je zegt '{fout} {modified_word}'. "
            f"Is '{modified_word}' een de-woord of een het-woord?"
        )

    # =========================================================
    # 5. DIE / DAT
    # =========================================================

    if fout_lower in {"die", "dat"} and modified_word is not None:

        change["mistake_type"] = 5

        # Relative pronoun
        if orig_vorm.get("PronType") == "Rel":

            return (
                f"Je zegt '{fout} {modified_word}'. "
                f"Is '{modified_word}' een de-woord of een het-woord?"
            )

        # Demonstrative
        return (
            f"Je zegt '{fout} {modified_word}'. "
            f"Is '{modified_word}' een de-woord of een het-woord?"
        )

    # =========================================================
    # 6. DAN / ALS
    # =========================================================

    if fout_lower in {"dan", "als"} or correctie_lower in {"dan", "als"}:

        change["mistake_type"] = 6

        if fout_lower == "als" and correctie_lower == "dan":
            return (
                f"Je zegt '{fout}'. Je vergelijkt hier twee dingen die niet gelijk zijn. "
                f"Zeg je 'als' of 'dan'?"
            )

        if fout_lower == "dan" and correctie_lower == "als":
            return (
                f"Je zegt '{fout}'. Wanneer twee dingen gelijk zijn. "
                f"Zeg je 'als' of 'dan'?"
            )

    # =========================================================
    # 7. NIET / GEEN
    # =========================================================

    if fout_lower in {"niet", "geen"} or correctie_lower in {"niet", "geen"}:

        change["mistake_type"] = 7

        if correctie_lower == "geen":
            return (
                f"Je zegt '{fout}'. "
                f"Je ontkent hier '{modified_word}'. "
                f"Zeg je 'niet' of 'geen'?"
            )

        if correctie_lower == "niet":
            return (
                f"Je zegt '{fout}'. "
                f"Wat wil je precies ontkennen: '{modified_word}' of de hele zin?"
                f"zeg je 'niet' of 'geen'?"
            )

    # =========================================================
    # 8. FIXED PREPOSITION
    # =========================================================

    # Examples:
    # interesse op geschiedenis -> interesse in geschiedenis

    if orig_pos == "ADP" and corr_pos == "ADP":

        change["mistake_type"] = 8

        return (
            f"Je zegt '{fout}'. "
            f"Welk voorzetsel hoort hier?"
        )

    # ---------------------------------------------------------
    # 9. PERSONAL PRONOUN
    # ---------------------------------------------------------

    if orig_pos == "PRON" and corr_pos == "PRON":

        change["mistake_type"] = 9

        if fout_lower in {"hij", "hem"}:
            return (
                f"Je zegt '{fout}'. "
                f"Zeg je hier: 'hij' of 'hem'?"
            )

        if fout_lower in {"zij", "haar"}:
            return (
                f"Je zegt '{fout}'. "
                f"Hoe verwijs je hier: 'zij' of 'haar'?"
            )

        if fout_lower in {"ik", "mij", "me"}:
            return (
                f"Je zegt '{fout}'. "
                f"Hoe verwijs je hier naar jezelf: 'ik' of 'mij'?"
            )

        if fout_lower in {"jij", "jou"}:
            return (
                f"Je zegt '{fout}'. "
                f"Hoe verwijs je hier: 'jij' of 'jou'?"
            )

        return (
            f"Je zegt '{fout}'. "
            f"Kijk goed naar de rol van dit woord in de zin."
        )

    # =========================================================
    # 10. GENERIC VERB FEEDBACK
    # =========================================================

    if corr_pos == "VERB" and lemma is not None:

        change["mistake_type"] = 10

        return (
            f"Je zegt '{fout}'. "
            f"Welke vorm van '{lemma}' past hier?"
        )

    # =========================================================
    # 11. GENERIC DETERMINER FEEDBACK
    # =========================================================

    if corr_pos == "DET" and modified_word is not None:

        change["mistake_type"] = 11

        return (
            f"Je zegt '{fout} {modified_word}'. "
            f"Kijk goed naar '{modified_word}'. Welke vorm hoort daarbij?"
        )

    # =========================================================
    # 12. GENERIC FALLBACK
    # =========================================================
    if change.get("operation") == "insert":
        return (
            f"Kijk nog eens goed naar je zin (\"" + zin + "\")"+ ", er ontbreekt wat in dit deel: \"" + meaningful_changes[0]['zin'] + "\""
        )

    if fout and correctie:
        return prompt_EULLM(feedback_prompt, stream_=True)
    return (
        prompt_EULLM(feedback_prompt, stream_=True)
    )

def check_grammar_easy(change, feedback_prompt):
    """
    Generate personalized Dutch feedback based on the output
    of extract_changes().

    Input:
        change: one dictionary returned by extract_changes()

    Output:
        str: personalized feedback/question
    """

    fout = change.get("fout", "").strip()
    fout_lower = fout.lower()
    correctie = change.get("correctie", "").strip()
    correctie_lower = correctie.lower()

    orig_pos = change.get("orig_woordsoort")
    corr_pos = change.get("woordsoort")

    orig_vorm = change.get("orig_vorm", {})
    corr_vorm = change.get("vorm", {})

    zin = change.get("zin", "")

    modified_word = change.get("modified_word")
    subject = change.get("subject")
    verb = change.get("verb")
    auxiliary = change.get("auxiliary")
    lemma = change.get("lemma")

    # Store the numbered mistake category selected below so callers can
    # persist or analyze the child's mistake alongside the feedback.
    change["mistake_type"] = None

    # =========================================================
    # 1. VERB AGREEMENT
    # =========================================================

    # Example:
    # De mensen loop ...
    # -> De mensen lopen ...

    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Fin"
        and subject is not None
    ):
        change["mistake_type"] = 1
        context = zin.strip()

        if "___" in context and fout and correctie:
            wrong_sentence = context.replace("___", fout, 1)
            correct_sentence = context.replace("___", correctie, 1)
            return f"Zeggen we '{wrong_sentence}' of '{correct_sentence}'?"

        if fout and correctie:
            return f"Zeggen we '{fout}' of '{correctie}' bij '{subject}'?"

        return f"Welke vorm past bij '{subject}'?"
    # =========================================================
    # 2. PAST PARTICIPLE AFTER AUXILIARY
    # =========================================================

    # Examples:
    # Ik heb ... gezoekt -> gezocht
    # Zij heeft ... verzendt -> verzonden
    # Hij is ... geglijdt -> gegleden

    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Part"
        and auxiliary is not None
        and lemma is not None
    ):
        change["mistake_type"] = 2
        return (
            f"Bijna! Als je zegt: \"{subject} {auxiliary} ... '{lemma}'\" dan zeggen we: \"{subject} {auxiliary} ... {correctie}.\" Kan jij mij vertellen wat de zin dan is?"
        )

    # =========================================================
    # 3. DE / HET
    # =========================================================

    if fout_lower in {"de", "het"} and modified_word is not None:

        change["mistake_type"] = 3

        return (
            f"Zeggen we '{fout} {modified_word}' of '{correctie} {modified_word}'? Probeer: \"{zin}\" te herhalen?"
        )

    # =========================================================
    # 4. DEZE / DIT
    # =========================================================

    if fout_lower in {"deze", "dit"} and modified_word is not None:

        change["mistake_type"] = 4

        return (
            f"Bij het wijzen naar '{modified_word}' zeggen we dan \" {fout} {modified_word}\" of \" {correctie} {modified_word}\"? Kun je dat herhalen?"
        )

    # =========================================================
    # 5. DIE / DAT
    # =========================================================

    if fout_lower in {"die", "dat"} and modified_word is not None:

        change["mistake_type"] = 5

        # Relative pronoun
        if orig_vorm.get("PronType") == "Rel":

            return (
                f"Bij het wijzen naar '{modified_word}' zeggen we dan \" {fout} {modified_word}\" of \" {correctie} {modified_word}\"? Kun je de zin herhalen?"
            )

        # Demonstrative
        return (
            f"Bij het wijzen naar '{modified_word}' zeggen we dan \" {fout} {modified_word}\" of \" {correctie} {modified_word}\"? Kun je de volledige zin herhalen?"
        )

    # =========================================================
    # 6. DAN / ALS
    # =========================================================

    if fout_lower in {"dan", "als"} or correctie_lower in {"dan", "als"}:

        change["mistake_type"] = 6

        if fout_lower == "als" and correctie_lower == "dan":
            return (
                f"Deze is moeilijk! De woorden zijn ongelijk, dus dan zeggen we '{correctie}'? Kan jij dat herhalen?"
            )

        if fout_lower == "dan" and correctie_lower == "als":
            return (
                f"Deze is moeilijk! De woorden zijn gelijk, dus dan zeggen we '{correctie}'? Kan jij dat herhalen?"
            )

    # =========================================================
    # 7. NIET / GEEN
    # =========================================================

    if fout_lower in {"niet", "geen"} or correctie_lower in {"niet", "geen"}:

        change["mistake_type"] = 7

        if correctie_lower == "geen":
            return (
                f"Als we '{modified_word}' ontkennen zeggen we 'geen'. Weet jij wat de zin dan wordt? Vul hem in: {zin}"
            )

        if correctie_lower == "niet":
            return (
                f"Als we de hele zin ontkennen zeggen we 'niet'. Weet jij wat de zin dan wordt? Vul hem in: {zin}"
            )

    # =========================================================
    # 8. FIXED PREPOSITION
    # =========================================================

    # Examples:
    # interesse op geschiedenis -> interesse in geschiedenis

    if orig_pos == "ADP" and corr_pos == "ADP":

        change["mistake_type"] = 8

        return (
            f"Welk voorzetsel hoort hier? Is dat '{fout}' of '{correctie}'? Kun je dat herhalen?"
        )

    # ---------------------------------------------------------
    # 9. PERSONAL PRONOUN
    # ---------------------------------------------------------

    if orig_pos == "PRON" and corr_pos == "PRON":

        change["mistake_type"] = 9

        if fout_lower in {"hij", "hem"}:
            return (
                f"Zeg je hier: 'hij' of 'hem'?"
            )

        if fout_lower in {"zij", "haar"}:
            return (
                f"Hoe verwijs je hier: 'zij' of 'haar'?"
            )

        if fout_lower in {"ik", "mij", "me"}:
            return (
                f"Hoe verwijs je hier naar jezelf: 'ik' of 'mij'?"
            )

        if fout_lower in {"jij", "jou"}:
            return (
                f"Hoe verwijs je hier: 'jij' of 'jou'?"
            )

        return (
            f"Zeggen we hier {fout} of {correctie}?"
        )

    # =========================================================
    # 10. GENERIC VERB FEEDBACK
    # =========================================================

    if corr_pos == "VERB" and lemma is not None:

        change["mistake_type"] = 10

        return (
            f"Welke vorm van '{lemma}' past hier? Is dat {fout} of {correctie}?"
        )

    # =========================================================
    # 11. GENERIC DETERMINER FEEDBACK
    # =========================================================

    if corr_pos == "DET" and modified_word is not None:

        change["mistake_type"] = 11

        return (
            f"Kijk goed naar '{fout}'. Hoe zeg je '{correctie}'?"
        )

    # =========================================================
    # 12. GENERIC FALLBACK
    # =========================================================
    if change.get("operation") == "insert":
        return (
            f"Kijk nog eens goed naar je zin, er mist wat in dit deel: \"" + meaningful_changes[0]['zin'] + "\""
        )

    if fout and correctie:
        return prompt_EULLM(feedback_prompt, stream_=True)
    return (
        prompt_EULLM(feedback_prompt, stream_=True)
    )

def get_mistake_type(change):
    """
    Classify a grammatical mistake based on extract_changes() output.

    Returns:
        int | None: mistake type (1-11), or None if unrecognized.
    """

    fout = change.get("fout", "").strip().lower()
    correctie = change.get("correctie", "").strip().lower()

    orig_pos = change.get("orig_woordsoort")
    corr_pos = change.get("woordsoort")

    corr_vorm = change.get("vorm") or {}

    modified_word = change.get("modified_word")
    subject = change.get("subject")
    auxiliary = change.get("auxiliary")
    lemma = change.get("lemma")

    # 1. Verb agreement
    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Fin"
        and subject is not None
    ):
        return 1

    # 2. Past participle after auxiliary
    if (
        corr_pos == "VERB"
        and corr_vorm.get("VerbForm") == "Part"
        and auxiliary is not None
        and lemma is not None
    ):
        return 2

    # 3. De / Het
    if fout in {"de", "het"} and modified_word is not None:
        return 3

    # 4. Deze / Dit
    if fout in {"deze", "dit"} and modified_word is not None:
        return 4

    # 5. Die / Dat
    if fout in {"die", "dat"} and modified_word is not None:
        return 5

    # 6. Dan / Als
    if fout in {"dan", "als"} or correctie in {"dan", "als"}:
        return 6

    # 7. Niet / Geen
    if fout in {"niet", "geen"} or correctie in {"niet", "geen"}:
        return 7

    # 8. Fixed preposition
    if orig_pos == "ADP" and corr_pos == "ADP":
        return 8

    # 9. Personal pronoun
    if orig_pos == "PRON" and corr_pos == "PRON":
        return 9

    # 10. Generic verb
    if corr_pos == "VERB" and lemma is not None:
        return 10

    # 11. Generic determiner
    if corr_pos == "DET" and modified_word is not None:
        return 11

    return None


def get_easy_feedback(zin):
    """Analyseer een zin en geef eenvoudige feedback op de eerste fout."""
    correctie, _, meaningful_changes = _analyze_grammar(zin)

    if not meaningful_changes:
        return {
            "correct": True,
            "feedback": "Je bent een topper! Goed gedaan.",
            "correction": correctie,
            "mistake_type": None
        }

    change = meaningful_changes[0]
    feedback_prompt = get_feedback_prompt(meaningful_changes)
    feedback = check_grammar_easy(change, feedback_prompt)

    return {
        "correct": False,
        "feedback": feedback,
        "correction": correctie,
        "mistake_type": change.get("mistake_type")
    }


def get_stage_one_feedback_prompt(change):
    return f"""Geef één subtiele, gerichte hint in het Nederlands voor een kind van 8.

Wijs alleen de plek aan waar het kind nog eens naar moet kijken. Geef niet de
correcte vorm en herschrijf de zin niet.

Probleemwoord: "{change['fout']}"
Zinsdeel met de fout open gelaten: "{change['zin']}"

Geef alleen de hint in één korte zin."""

def _analyze_grammar(zin):
    correction_prompt = get_correction_prompt(zin)
    correctie = prompt_EULLM(correction_prompt, stream_=False)

    print(f"correctie: {correctie}")
    changes = extract_changes(zin, correctie)
    meaningful_changes = [
        c for c in changes
        if any(t.pos_ not in {"SPACE", "PUNCT"}
            for t in nlp(c["fout"] + " " + c["correctie"]))
    ]

    print(f"changes: {meaningful_changes}")
    return correctie, changes, meaningful_changes

def get_stage_one_feedback(zin):
    correctie, _, meaningful_changes = _analyze_grammar(zin)

    if not meaningful_changes:
        return {
            "correct": True,
            "correction": correctie,
            "feedback": "Je bent een topper! Goed gedaan."
        }
    if meaningful_changes[0].get("operation") == "insert":
        feedback = "Kijk nog eens goed naar je zin (\"" + zin + "\")"+ ", er ontbreekt wat in dit deel: \"" + meaningful_changes[0]['zin'] + "\""
    else:
        feedback = "Kijk nog eens goed naar je zin (\"" + zin + "\")"+ ", vooral naar dit deel: \"" + meaningful_changes[0]['fout'] + "\""

    print(f"stage 1 feedback: {feedback}")

    return {
        "correct": False,
        "mistake_type": get_mistake_type(meaningful_changes[0]),
        "correction": correctie,
        "feedback": feedback
    }

def get_stage_three_feedback(zin):
    correctie, _, meaningful_changes = _analyze_grammar(zin)

    if not meaningful_changes:
        return {
            "correct": True,
            "feedback": "Je bent een topper! Goed gedaan.",
            "correction": correctie,
            "mistake_type": None
        }

    return {
        "correct": False,
        "mistake_type": get_mistake_type(meaningful_changes[0]),
        "correction": correctie,
        "feedback": f"{correctie} Kun je dat herhalen?"
    }

def get_feedback(zin):
    correctie, changes, meaningful_changes = _analyze_grammar(zin)

    if meaningful_changes:
        feedback_prompt = get_feedback_prompt(changes)
        feedback = genereer_feedback(meaningful_changes[0], feedback_prompt)
        print(f"feedback: {feedback}")
        return {
            "correct": False,
            "feedback": feedback,
            "correction": correctie,
            "mistake_type": meaningful_changes[0].get("mistake_type")
        }
    else: 
        return {
            "correct": True,
            "feedback": "Je bent een topper! Goed gedaan.",
            "correction": correctie,
            "mistake_type": None
        }
