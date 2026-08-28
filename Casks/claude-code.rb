cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.250"
  sha256 arm:          "506d7362a9c625306044879a9d91d8f33bd2eef963681b56be3295db5fe3e34b",
         x86_64:       "c247e9bf78fca8a081c8a746811d9641f4c38e727c341d253f359ddab6870f45",
         x86_64_linux: "2be252a00ac56e704d7fbf7e5e9ef1243584093334a861945238a0c27e84bdac",
         arm64_linux:  "0f4ff542f895526499ce23d8752c64cbb2ceb05a32cf6a1c0d1e31d82b20643d"

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
