"""Initial CareerLens schema"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table("jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("company", sa.String(length=180), nullable=False),
        sa.Column("location", sa.String(length=180), nullable=False),
        sa.Column("experience_level", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("apply_url", sa.String(length=1000), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_jobs_title", "jobs", ["title"])

    op.create_table("resumes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("owner_id", "sha256", name="uq_resume_owner_hash"),
        sa.UniqueConstraint("stored_filename", name="uq_resumes_stored_filename"))
    op.create_index("ix_resumes_owner_id", "resumes", ["owner_id"])
    op.create_index("ix_resumes_status", "resumes", ["status"])

    op.create_table("analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("resume_id", sa.Integer(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_analysis_results_resume_id", "analysis_results", ["resume_id"])

def downgrade():
    op.drop_index("ix_analysis_results_resume_id", table_name="analysis_results")
    op.drop_table("analysis_results")
    op.drop_index("ix_resumes_status", table_name="resumes")
    op.drop_index("ix_resumes_owner_id", table_name="resumes")
    op.drop_table("resumes")
    op.drop_index("ix_jobs_title", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
