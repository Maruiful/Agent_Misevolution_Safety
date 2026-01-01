package com.agent.misevolution.repository;

import agent.misevolution.domain.memory.ServiceExperience;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 服务经验数据访问层
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Mapper
public interface ServiceExperienceMapper extends BaseMapper<ServiceExperience> {

    /**
     * 根据实验ID和轮次查询经验
     */
    @Select("SELECT * FROM service_experiences WHERE experiment_id = #{experimentId} AND episode = #{episode}")
    ServiceExperience findByExperimentAndEpisode(@Param("experimentId") Long experimentId,
                                                  @Param("episode") Integer episode);

    /**
     * 查询实验的违规经验
     */
    @Select("SELECT * FROM service_experiences WHERE experiment_id = #{experimentId} AND is_violation = 1 ORDER BY episode DESC LIMIT #{limit}")
    List<ServiceExperience> findViolationsByExperiment(@Param("experimentId") Long experimentId,
                                                        @Param("limit") Integer limit);
}
