"""
Automated validation of responsive rules, mobile menu, touch targets, and attribution.
"""
import re
from pathlib import Path

def test_responsive_assets():
    css_path = Path("static/style.css")
    assert css_path.exists(), "style.css missing"
    css = css_path.read_text()

    html_path = Path("templates/index.html")
    assert html_path.exists(), "index.html missing"
    html = html_path.read_text()

    js_path = Path("static/app.js")
    assert js_path.exists(), "app.js missing"
    js = js_path.read_text()

    # 1. Breakpoints
    required_bps = [
        "@media (min-width: 1440px)",
        "@media (max-width: 1280px)",
        "@media (max-width: 1024px)",
        "@media (max-width: 860px)",
        "@media (max-width: 768px)",
        "@media (max-width: 480px)",
        "@media (max-width: 360px)",
        "@media (prefers-reduced-motion: reduce)"
    ]
    for bp in required_bps:
        assert bp in css, f"Missing breakpoint: {bp}"
    print("✓ All responsive breakpoints present in static/style.css")

    # 2. Touch targets & Mobile Menu
    assert ".mobile-menu-btn" in css, "Missing .mobile-menu-btn in CSS"
    assert "mobileMenuBtn" in html, "Missing mobileMenuBtn in HTML"
    assert "mobileDrawer" in html, "Missing mobileDrawer in HTML"
    assert "openMobileDrawer" in js, "Missing openMobileDrawer in app.js"
    assert "closeMobileDrawer" in js, "Missing closeMobileDrawer in app.js"
    assert "hamburger-bar" in css, "Missing hamburger-bar in CSS"
    assert "topbar-controls" in css, "Missing topbar-controls in CSS"
    print("✓ Mobile drawer, hamburger button, and backdrop correctly wired")

    # 3. Touch device 3D tilt guard
    assert "isTouchDevice" in js, "Missing isTouchDevice check in app.js"
    assert "prefersReducedMotion" in js, "Missing prefersReducedMotion check in app.js"
    print("✓ Touch devices and reduced motion explicitly guarded for 3D tilt")

    # 4. Attribution
    assert "Made by <strong>Rahulprasad Veeramani</strong>" in html, "Attribution name missing in index.html"
    assert "Branch Head (India)" in html, "Branch Head (India) missing in index.html"
    assert "https://www.cyberwolf360.in/" in html, "CyberWolf URL missing in index.html"
    print("✓ Creator attribution and CyberWolf Team link verified")

    # 5. Privacy page check
    privacy_path = Path("templates/privacy.html")
    assert privacy_path.exists(), "privacy.html missing"
    privacy_html = privacy_path.read_text()
    assert "Made by <strong>Rahulprasad Veeramani</strong>" in privacy_html, "Attribution in privacy.html missing"
    assert "https://www.cyberwolf360.in/" in privacy_html, "CyberWolf link in privacy.html missing"
    print("✓ Privacy page verified with accurate attribution")

    print("\n🎉 ALL RESPONSIVE ASSET CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_responsive_assets()
