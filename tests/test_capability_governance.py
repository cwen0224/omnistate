import importlib.util, json, os, stat, subprocess, sys, tempfile, time, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, "C:/dev/ROBOT")
spec = importlib.util.spec_from_file_location("guard", ROOT / ".omni/hooks/pre_tool_guard.py")
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)

from omnistate.governance.capability import audit as A
from omnistate.governance.capability.lifecycle import CapabilityGovernance
from hpvs import provenance, caption_stills
from hpvs.cli import main as hpvs_main
from hpvs.preview import build_native_options
from hpvs.config import HpvsError


def mkrepo():
    d = Path(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q"], cwd=d, check=True)
    for f in (".omnistaterc.json", "capabilities.manifest.json"):
        (d / f).write_text((ROOT / f).read_text(encoding="utf-8"), encoding="utf-8")
    (d / ".gitignore").write_text("node_modules/\n_outputs/\n")
    (d / "old.py").write_text("x=1\n")
    subprocess.run(["git", "add", "-A"], cwd=d, check=True)
    subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-qm", "i"], cwd=d, check=True)
    return d


def ev(root, tool, **args):
    return {"toolCall": {"name": tool, "args": args}, "workspacePaths": [str(root)]}


class GuardTests(unittest.TestCase):
    def setUp(self): self.r = mkrepo()
    def dec(self, tool, **a): return guard.decide(ev(self.r, tool, **a))["decision"]
    def code(self, tool, **a): return guard.decide(ev(self.r, tool, **a)).get("_code")

    def test_new_code_file_denied_anywhere(self):
        self.assertEqual(self.code("write_file", Path=str(self.r / "tools" / "extract_stills.py")), "NEW_CODE_FILE")
        self.assertEqual(self.code("write_file", Path="3_Caption/remotion/src/x.tsx"), "NEW_CODE_FILE")

    def test_existing_and_noncode_allowed(self):
        self.assertEqual(self.dec("edit_file", Path=str(self.r / "old.py")), "allow")
        self.assertEqual(self.dec("write_file", Path="notes/plan.md"), "allow")
        self.assertEqual(self.dec("write_file", Path="data/x.json"), "allow")

    def test_deny_reason_contains_alternative(self):
        reason = guard.decide(ev(self.r, "write_file", Path="tools/a.py"))["reason"]
        self.assertIn("python -m hpvs caption-stills", reason)

    def test_shell_code_creation(self):
        for c in ['echo "import os" > tools/a.py', 'Set-Content -Path tools/a.ps1 -Value "x"',
                  'Get-Content old.py | Set-Content tools/b.py', 'cp old.py tools/c.py',
                  'Rename-Item tmp.txt tools/d.py']:
            self.assertEqual(self.code("run_command", CommandLine=c), "SHELL_CODE_WRITE", c)

    def test_inline_interpreters(self):
        for c in ['python -c "import json"', 'python3 -c "print(1)"', 'node -e "1"',
                  '@\'\nprint(1)\n\'@ | python -', 'powershell -EncodedCommand AAAA']:
            self.assertEqual(self.code("run_command", CommandLine=c), "INLINE_INTERPRETER", c)

    def test_reserved_primitives(self):
        for c in ['npx remotion still src/index.tsx Comp out.png', 'npx.cmd remotion still a b c',
                  'chrome.exe --headless --screenshot=a.png http://x', 'ffmpeg -i a.mp4 -vframes 1 a.png',
                  'git status && npx remotion still a b c']:
            self.assertEqual(self.code("run_command", CommandLine=c), "RESERVED_PRIMITIVE", c)

    def test_legit_commands_pass(self):
        for c in ['python -m hpvs caption-stills --captions x.json', 'python.exe -m hpvs preview --timeline t.json --sheet',
                  'git commit -m "replace remotion still script"', 'rg "remotion still" .', 'python tools/existing.py',
                  'git status && python -m hpvs preview --timeline t.json', 'npx remotion studio',
                  'python -m omnistate.governance.capability audit', 'Get-Content old.py']:
            self.assertEqual(self.dec("run_command", CommandLine=c), "allow", c)

    def test_human_only_and_governance_tamper(self):
        self.assertEqual(self.code("run_command", CommandLine="python -m omnistate.governance.capability grant-extend --files a.py"), "HUMAN_ONLY")
        self.assertEqual(self.code("write_file", Path=".omni/state/session.json"), "GOVERNANCE_TAMPER")
        self.assertEqual(self.code("edit_file", Path=".omnistaterc.json"), "GOVERNANCE_TAMPER")
        self.assertEqual(self.code("run_command", CommandLine='Set-Content .omni/state/extend_ticket.json "{}"'), "GOVERNANCE_TAMPER")
        self.assertEqual(self.code("run_command", CommandLine='echo {} > .omni\\state\\session.json'), "GOVERNANCE_TAMPER")

    def test_extend_needs_valid_ticket_not_just_session(self):
        st = self.r / ".omni/state"; st.mkdir(parents=True)
        (st / "session.json").write_text(json.dumps({"mode": "extend"}))        # agent-forged session only
        self.assertEqual(self.dec("write_file", Path="hpvs/new.py"), "deny")
        (st / "extend_ticket.json").write_text(json.dumps({"files": ["hpvs/new.py"], "expires_at": time.time() + 600}))
        self.assertEqual(self.dec("write_file", Path="hpvs/new.py"), "allow")
        self.assertEqual(self.dec("write_file", Path="hpvs/other.py"), "deny")  # only declared files
        (st / "extend_ticket.json").write_text(json.dumps({"files": ["hpvs/new.py"], "expires_at": time.time() - 1}))
        self.assertEqual(self.dec("write_file", Path="hpvs/new.py"), "deny")    # expired

    def test_hook_process_protocol(self):
        p = subprocess.run([sys.executable, str(ROOT / ".omni/hooks/pre_tool_guard.py")], capture_output=True,
                           input=json.dumps(ev(self.r, "write_file", Path="tools/z.py")).encode("utf-8"))
        out = json.loads(p.stdout.decode("ascii"))
        self.assertEqual(out["decision"], "deny"); self.assertIn("BLOCKED", out["reason"])
        self.assertEqual(json.loads(subprocess.run([sys.executable, str(ROOT / ".omni/hooks/pre_tool_guard.py")],
                         capture_output=True, input=b"not json").stdout)["decision"], "allow")  # fail-open
        self.assertTrue((self.r / ".omni/logs/guard.jsonl").exists())


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.r = mkrepo(); self.gov = CapabilityGovernance(self.r)
        (self.r / "_outputs/W/headless_stills").mkdir(parents=True)
        (self.r / "_outputs/W/headless_stills/pre.png").write_bytes(b"pre")   # pre-existing artifact
        self.banner = self.gov.on_begin()

    def codes(self): return sorted((v.code, v.subject) for v in self.gov.on_audit())

    def test_begin_injects_mode_and_caps(self):
        self.assertIn("MODE: operate", self.banner); self.assertIn("hpvs.caption_stills", self.banner)

    def test_clean_run_passes(self): self.assertEqual(self.codes(), [])

    def test_catches_untracked_ignored_and_committed_scripts(self):
        (self.r / "tools").mkdir(); (self.r / "tools/extract.py").write_text("x")
        (self.r / "_outputs/W/hid.py").write_text("x")                     # git-ignored hiding place
        (self.r / "ok.md").write_text("x")
        (self.r / "node_modules/p").mkdir(parents=True); (self.r / "node_modules/p/i.js").write_text("x")
        (self.r / "committed.ps1").write_text("x")
        subprocess.run(["git", "add", "committed.ps1"], cwd=self.r, check=True)
        subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=n", "commit", "-qm", "c"], cwd=self.r, check=True)
        got = [s for c, s in self.codes() if c == "UNDECLARED_CODE_FILE"]
        self.assertEqual(sorted(got), ["_outputs/W/hid.py", "committed.ps1", "tools/extract.py"])

    def test_unsigned_artifact_and_signed_artifact(self):
        d = self.r / "_outputs/W/headless_stills"
        (d / "rogue.png").write_bytes(b"rogue")
        (d / "good.png").write_bytes(b"good")
        provenance.record(self.r, "r_t1", "hpvs.caption_stills", [d / "good.png"])
        self.assertEqual(self.codes(), [("UNSIGNED_ARTIFACT", "_outputs/W/headless_stills/rogue.png")])

    def test_tampering_after_signing_and_overwrite_of_existing(self):
        d = self.r / "_outputs/W/headless_stills"
        (d / "good.png").write_bytes(b"good")
        provenance.record(self.r, "r_t2", "hpvs.caption_stills", [d / "good.png"])
        (d / "good.png").write_bytes(b"edited by hand")
        (d / "pre.png").write_bytes(b"overwritten by script")             # pre-existing file silently replaced
        self.assertEqual(sorted(s for _, s in self.codes()),
                         ["_outputs/W/headless_stills/good.png", "_outputs/W/headless_stills/pre.png"])

    def test_extend_ticket_permits_declared_file(self):
        with self.assertRaises(PermissionError): self.gov.on_begin("extend")     # no ticket yet
        self.gov.grant_extend(["hpvs/new.py"]); self.gov.on_begin("extend")
        (self.r / "hpvs").mkdir(); (self.r / "hpvs/new.py").write_text("x"); (self.r / "hpvs/other.py").write_text("x")
        self.assertEqual(self.codes(), [("UNDECLARED_CODE_FILE", "hpvs/other.py")])  # declared ok, undeclared caught


class HpvsTests(unittest.TestCase):
    def setUp(self):
        self.r = mkrepo()
        (self.r / "3_Caption/remotion").mkdir(parents=True)
        self.bin = Path(tempfile.mkdtemp())
        py_fake = self.bin / "_fake_npx.py"
        py_fake.write_text("#!/usr/bin/env python3\nimport sys,json,re\n"
                           "a=sys.argv; out=a[5]; props=json.load(open([x for x in a if x.startswith('--props=')][0][8:],encoding='utf-8'))\n"
                           "if 'FAIL' in props['text']: sys.stderr.write('Error: composition crashed\\n'); sys.exit(1)\n"
                           "open(out,'wb').write(b'PNG'+props['text'].encode())\n", encoding="utf-8")
        if os.name == "nt":
            cmd_fake = self.bin / "npx.cmd"
            cmd_fake.write_text(f"@python \"{py_fake.resolve()}\" %*\n", encoding="utf-8")
        fake = self.bin / "npx"
        fake.write_text(py_fake.read_text(encoding="utf-8"), encoding="utf-8")
        fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{os.environ['PATH']}"
        self.caps = self.r / "_outputs/W/3_captions/v3.json"; self.caps.parent.mkdir(parents=True)
        self.caps.write_text(json.dumps({"captions": [
            {"caption_id": "c01", "text": "大字報一", "template_id": "t1"},
            {"caption_id": "c02/二", "text": "FAIL me"},
            {"caption_id": "c03", "text": "第三張"}]}, ensure_ascii=False), encoding="utf-8")

    def test_caption_stills_partial_report_ledger_and_audit(self):
        gov = CapabilityGovernance(self.r); gov.on_begin()
        cwd = os.getcwd(); os.chdir(self.r)
        try: code = hpvs_main(["caption-stills", "--captions", str(self.caps)])
        finally: os.chdir(cwd)
        self.assertEqual(code, 1)
        d = self.caps.parent / "headless_stills"
        rep = json.loads((d / "headless_preview_report.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["status"], "partial")
        self.assertEqual([x["ok"] for x in rep["results"]], [True, False, True])
        self.assertIn("composition crashed", rep["results"][1]["stderr_tail"])
        self.assertEqual(sorted(p.name for p in d.glob("*.png")), ["c01.png", "c03.png"])
        self.assertEqual(gov.on_audit(), [])                       # signed output passes the gate

    def test_ids_filter_and_unknown_id(self):
        res = caption_stills.run(self.r, str(self.caps), ids=["c01"])
        self.assertEqual(res["status"], "ok")
        with self.assertRaises(HpvsError): caption_stills.run(self.r, str(self.caps), ids=["nope"])

    def test_preview_options_and_unwired_adapter(self):
        n = build_native_options("t.json", every=2.0, range_="18:25", sheet=True)
        self.assertEqual((n["sample_mode"], n["cadence"], n["start"], n["end"], n["write_contact_sheet"]), ("interval", 2.0, 18.0, 25.0, True))
        self.assertEqual(build_native_options("t.json")["sample_mode"], "keyframe")
        with self.assertRaises(HpvsError): build_native_options("t.json", keyframes=True, every=1.0)
        (self.r / "t.json").write_text("{}")
        cwd = os.getcwd(); os.chdir(self.r)
        try: self.assertEqual(hpvs_main(["preview", "--timeline", "t.json"]), 3)
        finally: os.chdir(cwd)


if __name__ == "__main__":
    unittest.main(verbosity=1)
