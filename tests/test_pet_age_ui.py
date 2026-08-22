import json
import subprocess
import unittest


class PetAgeModeUiTests(unittest.TestCase):
    def run_node(self, expression: str):
        program = f"""
global.document = {{
    addEventListener() {{}},
    getElementById() {{ return null; }},
    querySelectorAll() {{ return []; }},
    querySelector() {{ return null; }}
}};
const petAge = require('./static/js/pet-age.js');
try {{
    const result = {expression};
    process.stdout.write(JSON.stringify(result));
}} catch (error) {{
    process.stdout.write(JSON.stringify({{ error: error.message }}));
}}
"""
        completed = subprocess.run(
            ["node", "-e", program],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_adoption_date_keeps_size_visible_but_disables_selection(self):
        state = self.run_node("petAge.getPetModeUiState('adoption-date', 'dog')")

        self.assertEqual(
            {
                "showSizeOptions": True,
                "disableSizeOptions": True,
                "showSizeExplanation": True,
            },
            state,
        )

    def test_birth_date_keeps_size_selection_available(self):
        state = self.run_node("petAge.getPetModeUiState('birth-date', 'dog')")

        self.assertEqual(
            {
                "showSizeOptions": True,
                "disableSizeOptions": False,
                "showSizeExplanation": False,
            },
            state,
        )

    def test_cat_never_exposes_dog_size_options(self):
        state = self.run_node("petAge.getPetModeUiState('adoption-date', 'cat')")

        self.assertEqual(
            {
                "showSizeOptions": False,
                "disableSizeOptions": False,
                "showSizeExplanation": False,
            },
            state,
        )


if __name__ == "__main__":
    unittest.main()
