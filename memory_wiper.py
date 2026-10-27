import os
import glob

class MemoryWiper:
    """
    Ensures absolute data privacy by purging all transient files, 
    PDF contracts, and temporary buffers before runner shutdown.
    """
    def __init__(self, target_extensions=None):
        self.target_extensions = target_extensions or ['*.pdf', '*.docx', '*.tmp']

    def purge_transient_files(self, directory="."):
        """
        Scans and securely shreds temporary output files from the local runner.
        """
        shredded_count = 0
        for ext in self.target_extensions:
            pattern = os.path.join(directory, ext)
            for file_path in glob.glob(pattern):
                try:
                    # Overwrite file content with zeros before deletion for high-grade security
                    if os.path.isfile(file_path):
                        file_size = os.path.getsize(file_path)
                        with open(file_path, "wb") as f:
                            f.write(b"\x00" * file_size)
                        os.remove(file_path)
                        print(f"Securely shredded and purged: {file_path}")
                        shredded_count += 1
                except Exception as e:
                    print(f"Error purging {file_path}: {e}")
        
        print(f"Memory wiper complete. Total transient assets purged: {shredded_count}")
        return shredded_count

if __name__ == "__main__":
    # Test execution layout
    wiper = MemoryWiper()
    wiper.purge_transient_files()
                      
