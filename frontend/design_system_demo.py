"""
Design System Demo

This script demonstrates the design system capabilities by generating
sample HTML with all the design tokens and components.
"""

from design_system import DesignSystem


def generate_demo_html() -> str:
    """Generate a demo HTML page showcasing the design system."""
    
    css = DesignSystem.generate_css()
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Design System Demo</title>
    {css}
</head>
<body style="padding: 2rem; background: {DesignSystem.COLORS['neutral_900']};">
    <h1 style="color: {DesignSystem.COLORS['primary_light']}; margin-bottom: 2rem;">
        Design System Demo
    </h1>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Status Badges
        </h2>
        <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
            <span class="status-running">⚡ RUNNING</span>
            <span class="status-completed">✅ COMPLETED</span>
            <span class="status-failed">❌ FAILED</span>
            <span class="status-queued">⏳ QUEUED</span>
            <span class="status-aborted">🛑 ABORTED</span>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Agent Cards
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="agent-card" style="border-color: {DesignSystem.COLORS['warning']};">
                <div style="font-size:24px">🔍</div>
                <div style="font-weight:600;">Research Agent</div>
                <div><span class="status-running">⚡ RUNNING</span></div>
                <div style="font-size:11px;color:{DesignSystem.COLORS['neutral_400']}">Model: gpt-4</div>
            </div>
            
            <div class="agent-card" style="border-color: {DesignSystem.COLORS['success']};">
                <div style="font-size:24px">🧠</div>
                <div style="font-weight:600;">Strategy Agent</div>
                <div><span class="status-completed">✅ COMPLETED</span></div>
                <div style="font-size:11px;color:{DesignSystem.COLORS['neutral_400']}">Model: gpt-4</div>
            </div>
            
            <div class="agent-card" style="border-color: {DesignSystem.COLORS['error']};">
                <div style="font-size:24px">⚖️</div>
                <div style="font-weight:600;">Critic Agent</div>
                <div><span class="status-failed">❌ FAILED</span></div>
                <div style="font-size:11px;color:{DesignSystem.COLORS['neutral_400']}">Model: gpt-4</div>
            </div>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Metric Boxes
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">
            <div class="metric-box">
                <div class="metric-value">8/10</div>
                <div class="metric-label">QA Score</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">12</div>
                <div class="metric-label">Sources</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">45</div>
                <div class="metric-label">Tasks</div>
            </div>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Verdict Badges
        </h2>
        <div style="display: flex; gap: 1rem;">
            <span class="verdict-badge verdict-APPROVED">APPROVED</span>
            <span class="verdict-badge verdict-REJECTED">REJECTED</span>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Log Panel
        </h2>
        <div class="log-panel">
            <div class="log-entry log-INFO">[2025-01-15 10:30:45] [orchestrator] Starting analysis pipeline</div>
            <div class="log-entry log-INFO">[2025-01-15 10:30:46] [research] Gathering market data</div>
            <div class="log-entry log-WARN">[2025-01-15 10:30:50] [strategy] Limited data available for sector</div>
            <div class="log-entry log-INFO">[2025-01-15 10:30:55] [critic] Evaluating strategy quality</div>
            <div class="log-entry log-ERROR">[2025-01-15 10:31:00] [qa] Validation failed: missing key metrics</div>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Glassmorphism Card
        </h2>
        <div class="glass-card" style="padding: 2rem; max-width: 500px;">
            <h3 style="color: {DesignSystem.COLORS['primary_light']}; margin-top: 0;">
                Glassmorphism Effect
            </h3>
            <p style="color: {DesignSystem.COLORS['neutral_300']}; line-height: 1.6;">
                This card demonstrates the glassmorphism design pattern with transparency,
                backdrop blur, and subtle borders. Hover over it to see the glow effect.
            </p>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Buttons
        </h2>
        <div style="display: flex; gap: 1rem;">
            <button class="btn-primary">Primary Button</button>
            <button class="btn-secondary">Secondary Button</button>
        </div>
    </section>
    
    <section style="margin-bottom: 3rem;">
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Animations
        </h2>
        <div style="display: flex; gap: 2rem; align-items: center;">
            <div class="agent-card animate-pulse" style="width: 150px; border-color: {DesignSystem.COLORS['warning']};">
                <div style="text-align: center;">Pulsing</div>
            </div>
            <div class="agent-card animate-fadeIn" style="width: 150px; border-color: {DesignSystem.COLORS['info']};">
                <div style="text-align: center;">Fade In</div>
            </div>
        </div>
    </section>
    
    <section>
        <h2 style="color: {DesignSystem.COLORS['neutral_200']}; margin-bottom: 1rem;">
            Color Palette
        </h2>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 1rem;">
            <div style="background: {DesignSystem.COLORS['primary']}; padding: 1rem; border-radius: {DesignSystem.RADIUS['md']}; text-align: center;">
                <div style="color: white; font-weight: 600;">Primary</div>
            </div>
            <div style="background: {DesignSystem.COLORS['success']}; padding: 1rem; border-radius: {DesignSystem.RADIUS['md']}; text-align: center;">
                <div style="color: white; font-weight: 600;">Success</div>
            </div>
            <div style="background: {DesignSystem.COLORS['warning']}; padding: 1rem; border-radius: {DesignSystem.RADIUS['md']}; text-align: center;">
                <div style="color: white; font-weight: 600;">Warning</div>
            </div>
            <div style="background: {DesignSystem.COLORS['error']}; padding: 1rem; border-radius: {DesignSystem.RADIUS['md']}; text-align: center;">
                <div style="color: white; font-weight: 600;">Error</div>
            </div>
            <div style="background: {DesignSystem.COLORS['info']}; padding: 1rem; border-radius: {DesignSystem.RADIUS['md']}; text-align: center;">
                <div style="color: white; font-weight: 600;">Info</div>
            </div>
        </div>
    </section>
</body>
</html>
"""
    return html


if __name__ == "__main__":
    html = generate_demo_html()
    
    # Save to file
    with open("design_system_demo.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("✅ Design system demo generated successfully!")
    print("📄 Open 'design_system_demo.html' in your browser to view the demo.")
    print(f"📊 Generated {len(html)} characters of HTML")
