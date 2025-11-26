import sys
from unittest.mock import MagicMock

# MOCK EVERYTHING that causes import errors
sys.modules["modelos"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["librosa"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["demucs"] = MagicMock()
sys.modules["demucs.apply"] = MagicMock()

# Configure mocks to return iterable values where expected
mock_modelos = sys.modules["modelos"]
mock_modelos.get_musicgen.return_value = (MagicMock(), MagicMock())

import unittest
import os
import shutil
import tempfile
from unittest.mock import patch, MagicMock
from procesamiento_audio import separate_stems

class TestSeparateStems(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for inputs and outputs
        self.test_dir = tempfile.mkdtemp()
        self.input_file = os.path.join(self.test_dir, "test_song.mp3")
        self.output_dir = os.path.join(self.test_dir, "outputs")
        
        # Create a dummy input file
        with open(self.input_file, "w") as f:
            f.write("dummy audio content")

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)

    @patch("procesamiento_audio.subprocess.Popen")
    def test_separate_stems_success(self, mock_popen):
        # 1. Setup Mock for subprocess
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Demucs output", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        # 2. Pre-create expected output files (simulating Demucs behavior)
        # separate_stems expects: out_dir/htdemucs/test_song/{stems}.wav
        song_name = "test_song"
        demucs_out = os.path.join(self.output_dir, "htdemucs", song_name)
        os.makedirs(demucs_out, exist_ok=True)
        
        expected_stems = ["vocals", "drums", "bass", "other"]
        for stem in expected_stems:
            stem_path = os.path.join(demucs_out, f"{stem}.wav")
            with open(stem_path, "wb") as f:
                f.write(b"dummy wav content" * 100) # Make sure size > 1000 bytes as per check

        # 3. Call the function
        result = separate_stems(self.input_file, self.output_dir)

        # 4. Assertions
        self.assertEqual(len(result), 4)
        self.assertIn("vocals", result)
        self.assertTrue(os.path.exists(result["vocals"]))
        
        # Verify subprocess was called correctly
        mock_popen.assert_called_once()
        args, _ = mock_popen.call_args
        command_list = args[0]
        self.assertEqual(command_list[0], "demucs")
        self.assertEqual(command_list[2], "htdemucs")
        self.assertEqual(command_list[4], self.output_dir)
        self.assertEqual(command_list[5], self.input_file)

    @patch("procesamiento_audio.subprocess.Popen")
    def test_separate_stems_subprocess_error(self, mock_popen):
        # Setup Mock to fail
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("", "Error executing demucs")
        process_mock.returncode = 1
        mock_popen.return_value = process_mock

        # Assert RuntimeError is raised
        with self.assertRaises(RuntimeError) as cm:
            separate_stems(self.input_file, self.output_dir)
        
        self.assertIn("Demucs falló", str(cm.exception))

    @patch("procesamiento_audio.subprocess.Popen")
    def test_separate_stems_missing_output(self, mock_popen):
        # Setup Mock to succeed but DON'T create files
        process_mock = MagicMock()
        process_mock.communicate.return_value = ("Done", "")
        process_mock.returncode = 0
        mock_popen.return_value = process_mock

        # Assert RuntimeError (or specific error about missing files)
        with self.assertRaises(RuntimeError) as cm:
            separate_stems(self.input_file, self.output_dir)
        
        # The function checks for the folder first
        self.assertTrue("no generó la carpeta" in str(cm.exception) or "stems salieron vacíos" in str(cm.exception))

if __name__ == "__main__":
    unittest.main()
