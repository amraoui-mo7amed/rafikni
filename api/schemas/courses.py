"""
Pydantic Schemas for Educational Courses, Videos, and Enrollments.
"""

from typing import List, Optional
from ninja import Schema
from .common import PaginationMetaSchema


class VideoItemSchema(Schema):
    id: int
    title: str
    description: Optional[str] = ""
    order: int
    is_free: bool
    duration: Optional[str] = None
    is_locked: bool = True
    video_url: Optional[str] = None


class CourseCardSchema(Schema):
    id: int
    title: str
    price: float
    teacher_name: str
    description: Optional[str] = ""
    thumbnail: Optional[str] = None
    tags: List[str] = []
    video_count: int = 0
    is_enrolled: bool = False
    enrollment_status: Optional[str] = None


class CourseDetailSchema(Schema):
    id: int
    title: str
    price: float
    teacher_name: str
    description: str
    thumbnail: Optional[str] = None
    tags: List[str] = []
    video_count: int = 0
    videos: List[VideoItemSchema] = []
    has_paid_access: bool = False
    enrollment_status: Optional[str] = None


class PaginatedCoursesSchema(Schema):
    items: List[CourseCardSchema]
    pagination: PaginationMetaSchema


class EnrollmentResponseSchema(Schema):
    enrollment_id: int
    status: str
    requires_payment: bool
    message: str


class EnrolledCourseSchema(Schema):
    enrollment_id: int
    status: str
    status_display: str
    enrolled_at: str
    course: CourseCardSchema


class VideoStreamSchema(Schema):
    id: int
    course_id: int
    course_title: str
    title: str
    description: Optional[str] = ""
    video_url: str
    duration: Optional[str] = None
    is_free: bool
