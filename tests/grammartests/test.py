from grammar.grammar import check

total_tests = 0
passed_tests = 0

positive_test_file = "tests/grammartests/positive_tests.txt"
negative_test_file = "tests/grammartests/negative_tests.txt"

def run_tests_from_file(file_path, expected):
	with open(file_path, "r") as f:
		for line in f:
			sentence = line.strip()
			if len(line) < 1 or line[0] == "#":
				continue

			if sentence:
				test(sentence, expected)

def test(sentence, expected):
	global total_tests, passed_tests
	result = check(sentence.split())


	if result["correct"] == expected:
		total_tests += 1
		passed_tests += 1
		#if not result["correct"]:
			#print(sentence)
			#print(f"Word index: {result['word_index']}, Mistake type: {result['mistake_type']}")
	else:
		print(f"FAIL: {sentence} (expected {expected}, got {result})")
		if not result["correct"]:
			print(f"Word index: {result['word_index']}, Mistake type: {result['mistake_type']}")
		total_tests += 1


run_tests_from_file(positive_test_file, True)
run_tests_from_file(negative_test_file, False)

print(f"Passed {passed_tests} out of {total_tests} tests")