from datetime import datetime
import stat
from typing import List, Literal, Optional
from uuid import uuid4
from fastapi import HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session, select
from src.db.courses import Course
from src.db.trail_runs import TrailRun, TrailRunCreate, TrailRunRead
from src.db.trail_steps import TrailStep
from src.db.trails import Trail, TrailCreate, TrailRead
from src.db.users import PublicUser
from src.services.orgs.schemas.orgs import PublicOrganization
from src.services.courses.chapters import get_coursechapters_meta


async def create_user_trail(
    request: Request,
    user: PublicUser,
    trail_object: TrailCreate,
    db_session: Session,
) -> Trail:
    statement = select(Trail).where(Trail.org_id == trail_object.org_id)
    trail = db_session.exec(statement).first()

    if trail:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trail already exists",
        )

    trail = Trail.from_orm(trail_object)

    trail.creation_date = str(datetime.now())
    trail.update_date = str(datetime.now())
    trail.org_id = trail_object.org_id
    trail.trail_uuid = str(f"trail_{uuid4()}")

    # create trail
    db_session.add(trail)
    db_session.commit()
    db_session.refresh(trail)

    return trail


async def get_user_trails(
    request: Request,
    user: PublicUser,
    db_session: Session,
) -> TrailRead:
    statement = select(Trail).where(Trail.user_id == user.id)
    trail = db_session.exec(statement).first()

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trail not found"
        )

    statement = select(TrailRun).where(TrailRun.trail_id == trail.id)
    trail_runs = db_session.exec(statement).all()

    trail_runs = [
        TrailRunRead(**trail_run.__dict__, steps=[]) for trail_run in trail_runs
    ]

    for trail_run in trail_runs:
        statement = select(TrailStep).where(TrailStep.trailrun_id == trail_run.id)
        trail_steps = db_session.exec(statement).all()

        trail_steps = [TrailStep(**trail_step.__dict__) for trail_step in trail_steps]
        trail_run.steps = trail_steps

        for trail_step in trail_steps:
            statement = select(Course).where(Course.id == trail_step.course_id)
            course = db_session.exec(statement).first()
            trail_step.data = dict(course=course)

    trail_read = TrailRead(
        **trail.dict(),
        runs=trail_runs,
    )

    return trail_read


async def get_user_trail_with_orgid(
    request: Request, user: PublicUser, org_id: int, db_session: Session
) -> TrailRead:
    statement = select(Trail).where(Trail.org_id == org_id, Trail.user_id == user.id)
    trail = db_session.exec(statement).first()

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trail not found"
        )

    statement = select(TrailRun).where(TrailRun.trail_id == trail.id)
    trail_runs = db_session.exec(statement).all()

    trail_runs = [
        TrailRunRead(**trail_run.__dict__, steps=[]) for trail_run in trail_runs
    ]

    for trail_run in trail_runs:
        statement = select(TrailStep).where(TrailStep.trailrun_id == trail_run.id)
        trail_steps = db_session.exec(statement).all()

        trail_steps = [TrailStep(**trail_step.__dict__) for trail_step in trail_steps]
        trail_run.steps = trail_steps

        for trail_step in trail_steps:
            statement = select(Course).where(Course.id == trail_step.course_id)
            course = db_session.exec(statement).first()
            trail_step.data = dict(course=course)

    trail_read = TrailRead(
        **trail.dict(),
        runs=trail_runs,
    )

    return trail_read


async def add_activity_to_trail(
    request: Request,
    user: PublicUser,
    course_id: int,
    activity_id: int,
    db_session: Session,
) -> TrailRead:
    
    # check if run already exists
    statement = select(TrailRun).where(TrailRun.course_id == course_id)
    trailrun = db_session.exec(statement).first()

    if trailrun:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="TrailRun already exists"
        )

    statement = select(Course).where(Course.id == course_id)
    course = db_session.exec(statement).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    statement = select(Trail).where(
        Trail.org_id == course.org_id, Trail.user_id == user.id
    )
    trail = db_session.exec(statement).first()

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trail not found"
        )

    statement = select(TrailRun).where(
        TrailRun.trail_id == trail.id, TrailRun.course_id == course.id
    )
    trailrun = db_session.exec(statement).first()

    if not trailrun:
        trailrun = TrailRun(
            trail_id=trail.id is not None,
            course_id=course.id is not None,
            org_id=course.org_id,
            user_id=user.id,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(trailrun)
        db_session.commit()
        db_session.refresh(trailrun)

    statement = select(TrailStep).where(
        TrailStep.trailrun_id == trailrun.id, TrailStep.activity_id == activity_id
    )
    trailstep = db_session.exec(statement).first()

    if not trailstep:
        trailstep = TrailStep(
            trailrun_id=trailrun.id is not None,
            activity_id=activity_id,
            course_id=course.id is not None,
            org_id=course.org_id,
            complete=False,
            teacher_verified=False,
            grade="",
            user_id=user.id,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(trailstep)
        db_session.commit()
        db_session.refresh(trailstep)

    statement = select(TrailRun).where(TrailRun.trail_id == trail.id)
    trail_runs = db_session.exec(statement).all()

    trail_runs = [
        TrailRunRead(**trail_run.__dict__, steps=[]) for trail_run in trail_runs
    ]

    for trail_run in trail_runs:
        statement = select(TrailStep).where(TrailStep.trailrun_id == trail_run.id)
        trail_steps = db_session.exec(statement).all()

        trail_steps = [TrailStep(**trail_step.__dict__) for trail_step in trail_steps]
        trail_run.steps = trail_steps

        for trail_step in trail_steps:
            statement = select(Course).where(Course.id == trail_step.course_id)
            course = db_session.exec(statement).first()
            trail_step.data = dict(course=course)

    trail_read = TrailRead(
        **trail.dict(),
        runs=trail_runs,
    )

    return trail_read


async def add_course_to_trail(
    request: Request,
    user: PublicUser,
    course_id: str,
    db_session: Session,
) -> TrailRead:
    
    # check if run already exists
    statement = select(TrailRun).where(TrailRun.course_id == course_id)
    trailrun = db_session.exec(statement).first()

    if trailrun:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="TrailRun already exists"
        )
    
    statement = select(Course).where(Course.id == course_id)
    course = db_session.exec(statement).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    statement = select(Trail).where(
        Trail.org_id == course.org_id, Trail.user_id == user.id
    )
    trail = db_session.exec(statement).first()

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trail not found"
        )

    statement = select(TrailRun).where(
        TrailRun.trail_id == trail.id, TrailRun.course_id == course.id
    )
    trail_run = db_session.exec(statement).first()

    if not trail_run:
        trail_run = TrailRun(
            trail_id=trail.id is not None,
            course_id=course.id is not None,
            org_id=course.org_id,
            user_id=user.id,
            creation_date=str(datetime.now()),
            update_date=str(datetime.now()),
        )
        db_session.add(trail_run)
        db_session.commit()
        db_session.refresh(trail_run)

    statement = select(TrailRun).where(TrailRun.trail_id == trail.id)
    trail_runs = db_session.exec(statement).all()

    trail_runs = [
        TrailRunRead(**trail_run.__dict__, steps=[]) for trail_run in trail_runs
    ]

    for trail_run in trail_runs:
        statement = select(TrailStep).where(TrailStep.trailrun_id == trail_run.id)
        trail_steps = db_session.exec(statement).all()

        trail_steps = [TrailStep(**trail_step.__dict__) for trail_step in trail_steps]
        trail_run.steps = trail_steps

        for trail_step in trail_steps:
            statement = select(Course).where(Course.id == trail_step.course_id)
            course = db_session.exec(statement).first()
            trail_step.data = dict(course=course)

    trail_read = TrailRead(
        **trail.dict(),
        runs=trail_runs,
    )

    return trail_read


async def remove_course_from_trail(
    request: Request,
    user: PublicUser,
    course_id: str,
    db_session: Session,
) -> TrailRead:
    statement = select(Course).where(Course.id == course_id)
    course = db_session.exec(statement).first()

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )

    statement = select(Trail).where(
        Trail.org_id == course.org_id, Trail.user_id == user.id
    )
    trail = db_session.exec(statement).first()

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trail not found"
        )

    statement = select(TrailRun).where(
        TrailRun.trail_id == trail.id, TrailRun.course_id == course.id
    )
    trail_run = db_session.exec(statement).first()

    if trail_run:
        db_session.delete(trail_run)
        db_session.commit()

    statement = select(TrailRun).where(TrailRun.trail_id == trail.id)
    trail_runs = db_session.exec(statement).all()

    trail_runs = [
        TrailRunRead(**trail_run.__dict__, steps=[]) for trail_run in trail_runs
    ]
    for trail_run in trail_runs:
        statement = select(TrailStep).where(TrailStep.trailrun_id == trail_run.id)
        trail_steps = db_session.exec(statement).all()

        trail_steps = [TrailStep(**trail_step.__dict__) for trail_step in trail_steps]
        trail_run.steps = trail_steps

        for trail_step in trail_steps:
            statement = select(Course).where(Course.id == trail_step.course_id)
            course = db_session.exec(statement).first()
            trail_step.data = dict(course=course)

    trail_read = TrailRead(
        **trail.dict(),
        runs=trail_runs,
    )

    return trail_read
