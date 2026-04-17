import pytest
from pathlib import Path

from eolib_ext.models import Extension
from eolib_ext.sources import resolve, resolve_extension_files


class TestFileSource:
    def test_resolves_existing_directory(self, tmp_path):
        ext_dir = tmp_path / "my-ext"
        ext_dir.mkdir()
        (ext_dir / "protocol.xml").write_text(
            '<?xml version="1.0"?><protocol></protocol>'
        )
        ext = Extension(type="file", name="my-ext", path=str(ext_dir))
        resolved = resolve(ext, tmp_path)
        assert resolved.name == "my-ext"
        assert Path(resolved.local_path) == ext_dir

    def test_resolves_relative_path(self, tmp_path):
        ext_dir = tmp_path / "my-ext"
        ext_dir.mkdir()
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        ext = Extension(type="file", name="my-ext", path="../my-ext")
        resolved = resolve(ext, config_dir)
        assert Path(resolved.local_path).resolve() == ext_dir.resolve()

    def test_raises_if_path_missing(self, tmp_path):
        ext = Extension(type="file", name="missing", path=str(tmp_path / "no-such-dir"))
        with pytest.raises(ValueError, match="does not exist"):
            resolve(ext, tmp_path)

    def test_raises_if_no_path_attribute(self, tmp_path):
        ext = Extension(type="file", name="no-path")
        with pytest.raises(ValueError, match="no 'path' attribute|has no 'path' attribute"):
            resolve(ext, tmp_path)

    def test_raises_for_unknown_type(self, tmp_path):
        ext = Extension(type="ftp", name="bad")
        with pytest.raises(ValueError, match="Unknown extension type"):
            resolve(ext, tmp_path)


class TestResolveExtensionFiles:
    def test_finds_root_protocol_xml(self, tmp_path):
        (tmp_path / "protocol.xml").write_text("<protocol/>")
        from eolib_ext.models import ResolvedExtension
        resolved = ResolvedExtension(name="test", local_path=str(tmp_path))
        files = resolve_extension_files(resolved)
        assert tmp_path / "protocol.xml" in files

    def test_root_file_comes_first(self, tmp_path):
        (tmp_path / "protocol.xml").write_text("<protocol/>")
        sub = tmp_path / "net" / "client"
        sub.mkdir(parents=True)
        (sub / "protocol.xml").write_text("<protocol/>")
        from eolib_ext.models import ResolvedExtension
        resolved = ResolvedExtension(name="test", local_path=str(tmp_path))
        files = resolve_extension_files(resolved)
        assert files[0] == tmp_path / "protocol.xml"

    def test_returns_empty_for_empty_directory(self, tmp_path):
        from eolib_ext.models import ResolvedExtension
        resolved = ResolvedExtension(name="test", local_path=str(tmp_path))
        files = resolve_extension_files(resolved)
        assert files == []
