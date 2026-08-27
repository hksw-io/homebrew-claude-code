cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.248"
  sha256 arm:          "a3f276daa51919f378bcd797d44f8e3d09653c2858123157d272de38952efeef",
         x86_64:       "35c21b09d049a4d040c511cd9f73de01df83aa1d4b35a43ae1353bde413b42bc",
         x86_64_linux: "3edee3cb054bd6823674fd60d5c0e442825b28ee8fbf815af2d16bf0de072e16",
         arm64_linux:  "76655a3731274f36236632b9acbcb9bef7055de20041c411b761856043fbc0df"

  url "https://downloads.claude.ai/claude-code-releases/#{version}/#{os}-#{arch}/claude",
      verified: "downloads.claude.ai/claude-code-releases/"
  name "Claude Code"
  desc "Terminal-based AI coding assistant"
  homepage "https://claude.com/product/claude-code"

  livecheck do
    url "https://downloads.claude.ai/claude-code-releases/latest"
    regex(/^v?(\d+(?:\.\d+)+)$/i)
  end

  binary "claude"

  zap trash: [
        "~/.cache/claude",
        "~/.claude.json*",
        "~/.config/claude",
        "~/.local/bin/claude",
        "~/.local/share/claude",
        "~/.local/state/claude",
        "~/Library/Caches/claude-cli-nodejs",
      ],
      rmdir: "~/.claude"
end
