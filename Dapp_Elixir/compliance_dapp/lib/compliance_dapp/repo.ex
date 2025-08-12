defmodule ComplianceDapp.Repo do
  use Ecto.Repo,
    otp_app: :compliance_dapp,
    adapter: Ecto.Adapters.Postgres
end
