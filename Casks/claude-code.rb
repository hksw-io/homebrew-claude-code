cask "claude-code" do
  arch arm: "arm64", intel: "x64"
  os macos: "darwin", linux: "linux"

  version "2.1.158"
  sha256 arm:          "536a0517fa64d48ddcbc8eb511a3d08027d47e06d148872332a8041d72c22768",
         x86_64:       "b7b33293702fb8e0a119b795d5af5178bd346fb46d4d7f161336d521f62d1451",
         arm64_linux:  "98807675a3ed5b7b775f7eaa81eda32cba2810b97e9db9f6f98d7bd658cec00e",
         x86_64_linux: "dd27008acd42700bac5762652ec83ff604bf9ae0786d4dde55d57a6866017fbe"

  url "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/#{version}/#{os}-#{arch}/claude",
      verified: "storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/"
  name "Claude Code"
  desc "Terminal-based AI coding assistant"
  homepage "https://www.anthropic.com/claude-code"

  livecheck do
    url "https://storage.googleapis.com/claude-code-dist-86c565f3-f756-42ad-8dfa-d59b1c096819/claude-code-releases/latest"
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
