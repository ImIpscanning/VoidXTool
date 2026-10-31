import sys
import os

class TermuxUtilities:
    @staticmethod
    def is_termux() -> bool:
        return 'ANDROID_ROOT' in os.environ

    @staticmethod
    def fix_dnspython():
        try:
            major = sys.version_info.major
            minor = sys.version_info.minor
            termux_lib_path = f"/data/data/com.termux/files/usr/lib/python{major}.{minor}/dns/resolver.py"
            site_packages_path = f"/data/data/com.termux/files/usr/lib/python{major}.{minor}/site-packages/dns/resolver.py"
            for path in [termux_lib_path, site_packages_path]:
                TermuxUtilities._fix(path)
        except Exception:
            pass

    @staticmethod
    def _fix(filepath: str) -> bool:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            new_content = content.replace('/etc/resolv.conf', '/data/data/com.termux/files/usr/etc/resolv.conf')
            if new_content != content:
                with open(filepath, 'w') as f:
                    f.write(new_content)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False