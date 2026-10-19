from enum import Enum
import numpy as np

def load_zelfstandig_naamwoorden(path="data/zelfstandig_naamwoorden.txt"):
	zelfstandig_naamwoorden = []
	zelfstandig_naamwoorden_ontelbaar = []
	with open(path, "r") as f:
		for line in f:
			is_ontelbaar = False
			if len(line.strip().split()) < 2 or line.strip().startswith("#"):
				continue

			if len(line.strip().split()) != 2:
				modifiers = line.strip().split()[2:]
				is_ontelbaar = "o" in modifiers


			lidwoord, woord = line.strip().split()[:2]
			if is_ontelbaar:
				zelfstandig_naamwoorden_ontelbaar.append([lidwoord, woord])
			else:
				zelfstandig_naamwoorden.append([lidwoord, woord])
				zelfstandig_naamwoorden.append(["een", woord])
	return zelfstandig_naamwoorden, zelfstandig_naamwoorden_ontelbaar

def endswith_any(word, endings):
	for ending in endings:
		if word.endswith(ending):
			return True
	return False

def generate_meervouden(zelfstandig_naamwoorden, overrides):
	meervouden = []
	for zelfstandig_naamwoord in zelfstandig_naamwoorden:
		lidwoord, woord = zelfstandig_naamwoord

		full_word = lidwoord + " " + woord
		if full_word in overrides:
			meervouden.append(overrides[full_word].split())
			continue

		if lidwoord == "de":
			if endswith_any(woord, ["el", "er", "en", "em"]):
				meervoud = ["de", woord + "s"]
			elif endswith_any(woord, ["a", "e", "o", "u", "y"]):
				meervoud = ["de", woord + "s"]
			else:
				meervoud = ["de", woord + "en"]
		elif lidwoord == "het":
			if woord.endswith("je"):
				meervoud = ["de", woord + "s"]
			else:
				meervoud = ["de", woord + "en"]
		else:
			continue

		meervouden.append(meervoud)
	return meervouden


overrides = {
	"de kat": "de katten",
	"het huis": "de huizen",
	"het kind": "de kinderen"
}

zelfstandig_naamwoorden, zelfstandig_naamwoorden_ontelbaar = load_zelfstandig_naamwoorden()
zelfstandig_naamwoorden_meervoud = generate_meervouden(zelfstandig_naamwoorden, overrides)

bijvoeglijke_naamwoorden_de = [
	"grote",
	"kleine",
	"mooie",
	"lelijke",
	"rode",
	"boze",
	"oranje",
	"lieve",
	"grijze",
	"lekkere",
	"gezonde",
]

bijvoeglijke_naamwoorden_het = [
	"groot",
	"klein",
	"mooi",
	"lelijk",
	"rood",
	"boos",
	"oranje",
	"lief",
	"grijs",
	"lekker",
	"gezond",
]

def load_werkwoorden(path="data/generated_werkwoorden.txt"):
	werkwoorden = []
	with open(path, "r") as f:
		for line in f:
			werkwoord_vormen = [word.strip().lower() for word in line.strip().split()]
			werkwoorden.append(werkwoord_vormen)

			if len(werkwoord_vormen) != 10:
				print(f"Warning: Expected 10 forms for verb, got {len(werkwoord_vormen)}: {werkwoord_vormen}")

	return werkwoorden

# infinitief, stam, jij,, hij/zij/het, wij, jullie, zij, verleden tijd, verleden tijd meervoud, voltooid deelwoord
werkwoorden = np.array(load_werkwoorden())

werkwoorden_infinitief = werkwoorden[:, 0]
werkwoorden_ik = werkwoorden[:, 1]
werkwoorden_jij = werkwoorden[:, 2]
werkwoorden_hij_zij_het = werkwoorden[:, 3]
werkwoorden_wij = werkwoorden[:, 4]
werkwoorden_jullie = werkwoorden[:, 5]
werkwoorden_zij = werkwoorden[:, 6]
werkwoorden_verleden_tijd = werkwoorden[:, 7]
werkwoorden_verleden_tijd_meervoud = werkwoorden[:, 8]
werkwoorden_voltooid_deelwoord = werkwoorden[:, 9]

tijden = [
	"toen",
	"nu",
	"straks",
	"gisteren",
	"morgen",
	"vandaag",
	"overmorgen",
	"eergisteren",
	"volgende week",
	"vorige week",
	"deze week",
	"komende week",
	"vorige week",
	"vandaag",
	"elke dag",
	"elke middag",
]

def laad_plaatsen_met_specifieke_voorzetsels(path="data/plaatsen_uitzonderingen.txt"):
	plaatsen_uitzonderingen = []
	with open(path, "r") as f:
		for line in f:
			if line.strip() == "" or line.strip().startswith("#"):
				continue
			plaatsen_uitzonderingen.append(line.strip())
	return plaatsen_uitzonderingen

plaatsen_uitzonderingen = laad_plaatsen_met_specifieke_voorzetsels()


def load_lines(path):
	lines = []
	with open(path, "r") as f:
		for line in f:
			if line.strip() == "" or line.strip().startswith("#"):
				continue
			lines.append(line.strip())
	return lines

voorzetsels = load_lines("data/voorzetsels.txt")


manieren = [
	"goed",
	"snel",
	"langzaam",
	"voorzichtig",
	"zorgvuldig",
	"precies",
]

punctuation = [".", ",", "!", "?", ";", ":"]

def check_match(zin, options):
	for option in options:
		option_list = option.split()
		if len(zin) < len(option_list):
			continue

		if zin[:len(option_list)] == option_list:
			return len(option_list)

	return None

class MistakeType(Enum):
	VERKEERDE_LIDWOORD = 1
	VERKEERDE_VOORNAAMWOORD = 2
	VERKEERDE_WERKWOORDVORM = 3
	VERKEERDE_BIJVOEGLIJK_NAAMWOORD = 4
	MISSEND_LIDWOORD = 5
	ONVOLLEDIGE_ZIN = 6

class GrammarError(Exception):
	def __init__(self, word_index, mistake_type):
		self.word_index = word_index
		self.mistake_type = mistake_type
		super().__init__("Grammar mistake")


def check(zin=["de", "beer", "loopt"]):
	
	try:
		result = check_onderwerp(0, clean(zin))
		return {
			"correct": result,
			"word_index": None,
			"mistake_type": None,
		}

	except GrammarError as e:
		return {
			"correct": False,
			"word_index": e.word_index,
			"mistake_type": e.mistake_type.name
		}





def clean(zin):
	zin_clean = []
	for woord in zin:
		# remove punctuation from existing words
		woord_clean = "".join([char for char in woord if char not in punctuation])
		zin_clean.append(woord_clean)
	return zin_clean


def check_onderwerp(depth, zin):
	if not zin:
		return False
	
	onderwerp = zin[0]
	if onderwerp.lower() in ["de", "het", "een"]:
		if check_onderwerp_derde_persoon(depth+1, onderwerp.lower(), zin[1:]):
			return True
	
	if onderwerp.lower() in ["ik", "jij", "hij", "zij", "het", "wij", "ze", "jullie"]:
		if onderwerp.lower() == "ik":
			return check_persoonsvorm(depth+1, "ik", zin[1:])

		if onderwerp.lower() == "jij":
			return check_persoonsvorm(depth+1, "jij", zin[1:])
		
		if onderwerp.lower() in ["hij", "zij", "het"]:
			return check_persoonsvorm(depth+1, "hij", zin[1:])

		if onderwerp.lower() in ["wij", "ze", "jullie"]:
			return check_persoonsvorm(depth+1, "wij", zin[1:])

	# mijn kat, mijn broer, zijn hond, haar huis, ons huis, jullie auto
	if onderwerp.lower() in ["mijn", "zijn", "haar", "ons", "onze", "jullie"]:

		allowed_lidwoorden = ["de", "het"]

		if onderwerp.lower() == "ons":
			allowed_lidwoorden = ["het"]
		elif onderwerp.lower() == "onze":
			allowed_lidwoorden = ["de"]

		zin_without_bns, number_bns = parse_bijvoeglijk_naamwoorden(depth+1, zin[1:])
		onderwerp = zin_without_bns[0]
			
		for zelfstandig_naamwoord in zelfstandig_naamwoorden:
			zn_lidwoord, zn_woord = zelfstandig_naamwoord

			if zn_woord == onderwerp:
				verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)

				if zn_lidwoord in allowed_lidwoorden:
					return check_persoonsvorm(depth+1+number_bns, "hij", zin_without_bns[1:])
				else:
					raise GrammarError(depth, MistakeType.VERKEERDE_VOORNAAMWOORD)
	
		for zelfstandig_naamwoord in zelfstandig_naamwoorden_meervoud:
			zn_lidwoord, zn_woord = zelfstandig_naamwoord

			if zn_woord == onderwerp:
				verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)

				if zn_lidwoord in allowed_lidwoorden:
					return check_persoonsvorm(depth+1+number_bns, "wij", zin_without_bns[1:])
				else:
					raise GrammarError(depth, MistakeType.VERKEERDE_VOORNAAMWOORD)
	

	# no correct subject found, check whether maybe a lidwoord is missing
	for lidwoord in ["de", "het", "een"]:
		try:
			result = check_onderwerp_derde_persoon(depth, lidwoord, zin)
		except GrammarError:
			continue
		if result:
			raise GrammarError(depth, MistakeType.MISSEND_LIDWOORD)
	return False


def verify_lidwoord_genders(depth, lidwoord, zn_lidwoord):
	if lidwoord == "een":
		# een is always correct, no need to check gender
		pass
	elif lidwoord in ["de", "het"]:
		# check agreement between the lidwoord and the noun
		if lidwoord != zn_lidwoord:
			raise GrammarError(depth, MistakeType.VERKEERDE_LIDWOORD)
	



def check_onderwerp_derde_persoon(depth, lidwoord, zin):
	if not zin:
		return False

	zin_without_bns, number_bns = parse_bijvoeglijk_naamwoorden(depth, zin[0:])
	onderwerp = zin_without_bns[0]

	for zelfstandig_naamwoord in zelfstandig_naamwoorden:
		zn_lidwoord, zn_woord = zelfstandig_naamwoord
		
		# found the correct noun
		if zn_woord == onderwerp:
			# check whether the lidwoord and bijvoeglijk naamwoord agree with the noun
			verify_lidwoord_genders(depth-1, lidwoord, zn_lidwoord)

			return check_persoonsvorm(depth+1+number_bns, "hij", zin_without_bns[1:])

	for zelfstandig_naamwoord in zelfstandig_naamwoorden_meervoud:
		zn_lidwoord, zn_woord = zelfstandig_naamwoord

		# found the correct noun
		if zn_woord == onderwerp:
			if lidwoord == "een":
				raise GrammarError(depth-1, MistakeType.VERKEERDE_LIDWOORD)

			# check agreement between the lidwoord and the noun
			verify_lidwoord_genders(depth, lidwoord, zn_lidwoord)
			
			return check_persoonsvorm(depth+1+number_bns, "wij", zin_without_bns[1:])
		
	return False


def is_werkwoord(depth, zin):
	for vorm in [werkwoorden_ik, werkwoorden_jij, werkwoorden_hij_zij_het, werkwoorden_infinitief, werkwoorden_voltooid_deelwoord]:
		result = check_match(zin, vorm)
		if result is not None:
			# If a match is found, return True to indicate that the word is a verb
			return True
	return False


def check_persoonsvorm(depth, verwachte_vorm, zin):
	if not zin:
		return False
	
	if verwachte_vorm.lower() == "ik":
		result = check_match(zin, werkwoorden_ik)
		if result is not None:
			return check_midden(depth+result, zin[result:])
		else:
			if is_werkwoord(depth+1, zin):
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
			else:
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)

		
	if verwachte_vorm.lower() == "jij":
		result = check_match(zin, werkwoorden_jij)
		if result is not None:
			return check_midden(depth+result, zin[result:])
		else:
			if is_werkwoord(depth+1, zin):
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
			else:
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)

		
	if verwachte_vorm.lower() == "hij":
		result = check_match(zin, werkwoorden_hij_zij_het)

		if result is not None:
			return check_midden(depth+result, zin[result:])
		else:
			if is_werkwoord(depth+1, zin):
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
			else:
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)

		
	if verwachte_vorm.lower() == "wij":
		result = check_match(zin, werkwoorden_infinitief)

		if result is not None:
			return check_midden(depth+result, zin[result:])
		else:
			if is_werkwoord(depth+1, zin):
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
			else:
				raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
		
	return False


def check_midden(depth, zin):
	if len(zin) == 0:
		return True

	if check_lijdend_voorwerp_begin_midden(depth, zin):
		return True
	return False

def is_lidwoord(word):
	return word.lower() in ["de", "het", "een"]

def check_lidwoord_bns_noun_combo(depth, zin, next_function):
	if not is_lidwoord(zin[0].lower()):
		zin_without_bns, number_bns = parse_bijvoeglijk_naamwoorden_het(depth, zin)
		# ontelbaar does not require a specific lidwoord
		for zelfstandig_naamwoord in zelfstandig_naamwoorden_ontelbaar:
			zn_lidwoord, zn_woord = zelfstandig_naamwoord
			if zn_woord == zin_without_bns[0].lower():
				return next_function(depth+1+number_bns, zin_without_bns[1:])

	# problem: always removes one word for lidwoord but might not be present for uncountable nouns
	zin_without_bns, number_bns = parse_bijvoeglijk_naamwoorden(depth+1, zin[1:])
	if len(zin_without_bns) == 0:
		raise GrammarError(depth, MistakeType.ONVOLLEDIGE_ZIN)
	for zelfstandig_naamwoord in zelfstandig_naamwoorden:
		zn_lidwoord, zn_woord = zelfstandig_naamwoord
		if zn_woord == zin_without_bns[0].lower():
			# found the right noun, verify agreement with lidwoord and bijvoeglijk naamwoord
			verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)
			return next_function(depth+1+number_bns, zin_without_bns[1:])
			
			return next_function(depth+1+number_bns, zin_without_bns[1:])

	for zelfstandig_naamwoord in zelfstandig_naamwoorden_meervoud:
		zn_lidwoord, zn_woord = zelfstandig_naamwoord
		if zn_woord == zin_without_bns[0].lower():
			# found the right noun, verify agreement with lidwoord and bijvoeglijk naamwoord
			verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)
			return next_function(depth+1+number_bns, zin_without_bns[1:])

	return False

def check_voorwerp(depth, zin, self_call, next_function, do_recursive_lidwoord_check=True):
	# Example: check if the first word indicates a direct object
	if zin[0].lower() in ["de", "het", "een"]:
		result = check_lidwoord_bns_noun_combo(depth, zin, next_function)
		if result:
			return result
		
	result = check_lidwoord_bns_noun_combo(depth, zin, next_function)
	if result:
		return result


	if zin[0].lower() in ["mijn", "zijn", "haar", "ons", "onze", "jullie"]:

		onderwerp = zin[0]

		allowed_lidwoorden = ["de", "het"]

		if onderwerp.lower() == "ons":
			allowed_lidwoorden = ["het"]
		elif onderwerp.lower() == "onze":
			allowed_lidwoorden = ["de"]


		zin_without_bns, number_bns = parse_bijvoeglijk_naamwoorden(depth+1, zin[1:])
		onderwerp = zin_without_bns[0]


		for zelfstandig_naamwoord in zelfstandig_naamwoorden:
			zn_lidwoord, zn_woord = zelfstandig_naamwoord

			if zn_woord == onderwerp:
				verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)

				if zn_lidwoord in allowed_lidwoorden:
					return next_function(depth, zin[2:])
				else:
					raise GrammarError(depth, MistakeType.VERKEERDE_VOORNAAMWOORD)
	
		for zelfstandig_naamwoord in zelfstandig_naamwoorden_meervoud:
			zn_lidwoord, zn_woord = zelfstandig_naamwoord

			if zn_woord == onderwerp:
				verify_lidwoord_genders(depth, zin[0].lower(), zn_lidwoord)

				if zn_lidwoord in allowed_lidwoorden:
					return next_function(depth, zin[2:])
				else:
					raise GrammarError(depth, MistakeType.VERKEERDE_VOORNAAMWOORD)

	# no correct lijdend voorwerp found, check whether maybe a lidwoord is missing
	if do_recursive_lidwoord_check:
		for lidwoord in ["de", "het", "een"]:
			try:
				result = None
				new_zin = [lidwoord]
				new_zin.extend(zin)
				result = self_call(depth+1, new_zin, do_recursive_lidwoord_check=False)
			except GrammarError:
				continue
			if result:
				raise GrammarError(depth, MistakeType.MISSEND_LIDWOORD)
	
	return next_function(depth, zin)

# lijdend voorwerp mag aan begin of eind van het midden staan
def check_lijdend_voorwerp_begin_midden(depth, zin, do_recursive_lidwoord_check=True):
	if not zin:
		return True

	return check_voorwerp(depth, zin, self_call=check_lijdend_voorwerp_begin_midden, next_function=check_tijd, do_recursive_lidwoord_check=do_recursive_lidwoord_check)



def parse_bijvoeglijk_naamwoorden(depth, zin):
	i = 0
	while i < len(zin):
		is_de_bn = zin[i].lower() in bijvoeglijke_naamwoorden_de
		is_het_bn = zin[i].lower() in bijvoeglijke_naamwoorden_het

		if is_het_bn and not is_de_bn:
			raise GrammarError(depth+i, MistakeType.VERKEERDE_BIJVOEGLIJK_NAAMWOORD)

		if not is_de_bn:
			break
		i += 1
	return zin[i:], i

def parse_bijvoeglijk_naamwoorden_het(depth, zin):
	i = 0
	while i < len(zin):
		is_de_bn = zin[i].lower() in bijvoeglijke_naamwoorden_de
		is_het_bn = zin[i].lower() in bijvoeglijke_naamwoorden_het

		if is_de_bn and not is_het_bn:
			raise GrammarError(depth+i, MistakeType.VERKEERDE_BIJVOEGLIJK_NAAMWOORD)

		if not is_het_bn:
			break
		i += 1
	return zin[i:], i


def check_tijd(depth, zin):
	if len(zin) == 0:
		return True
	
	if not zin:
		return False
	
	# Example: check if the first word indicates time
	result = check_match(zin, tijden)

	if result is not None:
		return check_manier(depth+result, zin[result:])
	
	return check_manier(depth, zin)


def check_manier(depth, zin):
	if not zin:
		return False
	
	result = check_match(zin, manieren)
	if result is not None:
		return check_plaats(depth+result, zin[result:])
	
	return check_plaats(depth, zin)


def check_plaats(depth, zin):
	if not zin:
		return False

	result = check_match(zin, plaatsen_uitzonderingen)
	if result is not None:
		return check_lijdend_voorwerp_eind_midden(depth+result, zin[result:])

	if zin[0].lower() in voorzetsels:
		return check_lijdend_voorwerp_eind_midden(depth+1, zin[1:])

	
	return check_lijdend_voorwerp_eind_midden(depth, zin)


# lijdend voorwerp mag aan begin of eind van het midden staan
def check_lijdend_voorwerp_eind_midden(depth, zin, do_recursive_lidwoord_check=True):
	if not zin:
		return True

	return check_voorwerp(depth, zin, self_call=check_lijdend_voorwerp_eind_midden, next_function=check_rechterzijde, do_recursive_lidwoord_check=do_recursive_lidwoord_check)


def check_rechterzijde(depth, zin):
	if len(zin) == 0:
		return True

	return check_overige_werkwoorden(depth, zin)


def check_overige_werkwoorden(depth, zin):
	if not zin:
		return False
	

	result = check_match(zin, werkwoorden_infinitief)

	if result is not None:
		return True
	

	result = check_match(zin, werkwoorden_voltooid_deelwoord)

	if result is not None:
		return True

	if is_werkwoord(depth, zin):
		raise GrammarError(depth, MistakeType.VERKEERDE_WERKWOORDVORM)
	
	return False
