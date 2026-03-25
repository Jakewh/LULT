# Contributing

Thank you for considering a contribution.

## Basic Workflow

1. Fork the repository
2. Create a feature branch
3. Make focused changes
4. Test locally
5. Open a pull request

## Local Validation

```bash
python3 -m py_compile Lult.py
./run.sh
```

For packaging checks:

```bash
./build_single_linux.sh
```

## Coding Notes

- Keep UI changes consistent with existing style
- Avoid unrelated refactors in feature PRs
- Update docs when behavior changes
- Keep Linux paths and scripts tested on target distro

## PR Checklist

- [ ] Code runs without errors
- [ ] No unrelated file changes
- [ ] README/DEPENDENCIES updated if needed
- [ ] Build/install scripts still work
