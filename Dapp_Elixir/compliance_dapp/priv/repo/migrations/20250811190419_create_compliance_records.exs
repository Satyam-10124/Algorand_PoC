defmodule ComplianceDapp.Repo.Migrations.CreateComplianceRecords do
  use Ecto.Migration

  def change do
    create table(:compliance_records) do
      add :entity_id, :string, null: false
      add :compliance_type, :string, null: false
      add :status, :string, null: false, default: "pending"
      add :data_hash, :string
      add :algorand_tx_id, :string
      add :app_id, :integer
      add :verified_at, :naive_datetime
      add :metadata, :map

      timestamps()
    end

    create index(:compliance_records, [:entity_id])
    create index(:compliance_records, [:algorand_tx_id])
  end
end
